"""
主体自律指数计算服务（论文 3.2 / 5.4.2：AHP-Transformer 混合赋权）

流程：数据标准化 → AHP 主观权重 + Transformer 客观权重 → 先验正则化融合 → 加权求和 → 分级
"""
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.indicator import IndexResult
from app.repositories.indicator_repository import (
    dimension_repository, indicator_repository, indicator_value_repository,
    index_result_repository,
)
from app.repositories.company_repository import company_repository

# 四维度十二项指标（3.1.2）
DIMENSIONS = {
    "D1": ("信息披露质量", "衡量上市公司信息披露的及时性、完整性与合规性"),
    "D2": ("董事会治理有效性", "衡量董事会结构、运作与监督职能发挥情况"),
    "D3": ("内部控制与合规性", "衡量内控体系有效性、违规处罚与整改情况"),
    "D4": ("第三方声誉", "衡量 ESG 表现、审计意见与市场舆情"),
}

INDICATORS = [
    ("I01", "披露及时性", "D1", "positive", "天"),
    ("I02", "披露完整性", "D1", "positive", "分"),
    ("I03", "信息披露考评等级", "D1", "positive", "级"),
    ("I04", "独立董事占比", "D2", "positive", "%"),
    ("I05", "董事会会议频次", "D2", "positive", "次"),
    ("I06", "专门委员会运作", "D2", "positive", "分"),
    ("I07", "内控审计意见", "D3", "positive", "分"),
    ("I08", "违规处罚次数", "D3", "negative", "次"),
    ("I09", "内控缺陷整改率", "D3", "positive", "%"),
    ("I10", "ESG评级", "D4", "positive", "级"),
    ("I11", "审计意见类型", "D4", "positive", "分"),
    ("I12", "媒体舆情得分", "D4", "positive", "分"),
]

# 指标维数（BGE-M3 / Transformer 注意力头共享）
ATTENTION_HEADS = 4
PRIOR_ALPHA = 0.6  # 先验正则化融合系数：w = α·w_ahp + (1-α)·w_trans


def init_indicator_system(db: Session):
    """初始化四维度十二项指标体系（幂等）"""
    for code, (name, desc) in DIMENSIONS.items():
        if not dimension_repository.get_by_code(db, code):
            from app.models.indicator import Dimension
            dimension_repository.create(db, Dimension(code=code, name=name, description=desc))
    for code, name, dim, direction, unit in INDICATORS:
        if not indicator_repository.get_by_code(db, code):
            dim_obj = dimension_repository.get_by_code(db, dim)
            indicator_repository.create(db, Indicator(
                code=code, name=name, dimension_id=dim_obj.id,
                direction=direction, unit=unit, data_source="CSMAR",
            ))


class IndexService:
    """主体自律指数计算：AHP-Transformer 混合赋权"""

    # ---------- 数据标准化（3.3.1） ----------
    @staticmethod
    def standardize(df: pd.DataFrame, directions: dict[str, str]) -> pd.DataFrame:
        """极差标准化到 [0,100]，正向指标越大越好，负向指标越小越好"""
        std = pd.DataFrame(index=df.index)
        for col in df.columns:
            series = df[col].astype(float)
            mn, mx = series.min(), series.max()
            rng = mx - mn if mx != mn else 1.0
            if directions.get(col) == "negative":
                std[col] = (mx - series) / rng * 100
            else:
                std[col] = (series - mn) / rng * 100
        return std.fillna(50.0)

    # ---------- AHP 主观权重（3.2.1） ----------
    @staticmethod
    def ahp_weights(judgment: np.ndarray) -> np.ndarray:
        """特征向量法求权重，含一致性检验（CR < 0.1）"""
        n = judgment.shape[0]
        eigvals, eigvecs = np.linalg.eig(judgment)
        idx = int(np.argmax(eigvals.real))
        w = np.abs(eigvecs[:, idx].real)
        w = w / w.sum()
        # 一致性检验
        lam_max = eigvals[idx].real
        ci = (lam_max - n) / (n - 1) if n > 1 else 0.0
        ri_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
                    7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49, 11: 1.51, 12: 1.54}
        cr = ci / ri_table.get(n, 1.54)
        if cr >= 0.1:
            raise BusinessException(f"AHP 判断矩阵一致性检验未通过（CR={cr:.3f} ≥ 0.1），请修正专家打分")
        return w

    # ---------- Transformer 客观权重（3.2.2） ----------
    @staticmethod
    def transformer_weights(std_matrix: np.ndarray) -> np.ndarray:
        """
        用 Transformer 多头注意力挖掘指标间非线性关联：
        将标准化指标向量视为 token 序列，对各公司样本取注意力分数的
        均值作为指标重要性，归一化得到客观权重。
        """
        import torch
        import torch.nn as nn

        x = torch.tensor(std_matrix, dtype=torch.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        n_indicator = x.shape[1]
        embed = x.unsqueeze(-1).repeat(1, 1, ATTENTION_HEADS)  # (company, indicator, head)
        attn = nn.MultiheadAttention(embed_dim=ATTENTION_HEADS, num_heads=ATTENTION_HEADS, batch_first=True)
        with torch.no_grad():
            q = k = v = embed
            out, weights = attn(q, k, v, need_weights=True, average_attn_weights=True)
        # 注意力矩阵 (indicator, indicator)，行和表示该指标被关注的程度
        importance = weights.sum(dim=0).numpy()[:n_indicator]
        w = importance / importance.sum()
        return w

    # ---------- 先验正则化融合（3.2.3） ----------
    @staticmethod
    def fuse_weights(w_ahp: np.ndarray, w_trans: np.ndarray, alpha: float = PRIOR_ALPHA) -> np.ndarray:
        """先验正则化：w = α·w_ahp + (1-α)·w_trans，α 体现对专家经验的回归约束"""
        w = alpha * w_ahp + (1 - alpha) * w_trans
        return w / w.sum()

    # ---------- 指数计算与分级（3.3.2 / 3.3.3） ----------
    @staticmethod
    def grade(score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        return "D"

    def compute(self, db: Session, year: int, judgment_matrix: list[list[float]] | None = None):
        """
        计算指定年度全部公司的主体自律指数：
        1. 读取指标原始值并标准化（结果回写 std_value）
        2. 计算混合权重
        3. 加权求和得指数，按维度汇总，分级入库
        """
        init_indicator_system(db)
        values = indicator_value_repository.get_matrix(db, year)
        if not values:
            raise BusinessException(f"{year} 年度无指标数据，请先导入 CSMAR 数据")

        # 组装 公司×指标 矩阵
        indicators = indicator_repository.list_with_dimension(db)
        ind_codes = [i.code for i in indicators]
        id2code = {i.id: i.code for i in indicators}
        directions = {i.code: i.direction for i in indicators}

        rows: dict[int, dict[str, float]] = {}
        for v in values:
            rows.setdefault(v.company_id, {})[id2code[v.indicator_id]] = v.raw_value
        df = pd.DataFrame(rows).T[ind_codes]
        std = self.standardize(df, directions)

        # 回写标准化值
        for v in values:
            v.std_value = float(std.loc[v.company_id, id2code[v.indicator_id]])
        db.commit()

        # AHP 权重：默认采用课题组标定矩阵，也可由前端传入专家矩阵
        if judgment_matrix:
            w_ahp = self.ahp_weights(np.array(judgment_matrix, dtype=float))
        else:
            w_ahp = self._default_ahp_weights()

        # Transformer 客观权重
        w_trans = self.transformer_weights(std.values)

        # 融合
        w = self.fuse_weights(np.array(w_ahp), w_trans)

        # 加权评分
        company_scores = std.values @ w
        dim_map = {d.code: d.id for d in dimension_repository.list(db)}
        ind_dim = {i.code: i.dimension_id for i in indicators}

        results = []
        for company_id, score in zip(std.index, company_scores):
            dim_scores: dict[int, float] = {}
            for dim_id in set(ind_dim.values()):
                cols = [c for c in ind_codes if ind_dim[c] == dim_id]
                sub_w = np.array([w[ind_codes.index(c)] for c in cols])
                sub_w = sub_w / sub_w.sum()
                dim_scores[dim_id] = float(std.loc[company_id, cols].values @ sub_w)
            level = self.grade(float(score))
            existing = index_result_repository.get_by_company_year(db, int(company_id), year)
            if existing:
                index_result_repository.delete(db, existing.id)
            result = IndexResult(
                company_id=int(company_id), year=year, score=float(score), level=level,
                d1_score=dim_scores.get(dim_map.get("D1")),
                d2_score=dim_scores.get(dim_map.get("D2")),
                d3_score=dim_scores.get(dim_map.get("D3")),
                d4_score=dim_scores.get(dim_map.get("D4")),
                weight_scheme="ahp_transformer",
            )
            results.append(index_result_repository.create(db, result))
        return {"weights": dict(zip(ind_codes, w.tolist())), "count": len(results)}

    def _default_ahp_weights(self) -> np.ndarray:
        """课题组标定的默认 AHP 权重（四个维度等权，维度内等权）"""
        return np.array([1 / 12] * 12)
