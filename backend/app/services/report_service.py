"""
评价报告生成与导出服务（5.4.5）

整合指数评分 + 多维度评价 + 证据溯源，生成结构化评价报告（HTML/PDF）
"""
import io
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.repositories.evaluation_repository import evaluation_evidence_repository
from app.repositories.indicator_repository import index_result_repository
from app.services.company_service import company_service
from app.services.evaluation_service import evaluation_service

DIM_NAMES = {"D1": "信息披露质量", "D2": "董事会治理有效性",
             "D3": "内部控制与合规性", "D4": "第三方声誉"}


class ReportService:
    def build_report_data(self, db: Session, stock_code: str, year: int) -> dict:
        """汇总报告所需的全部数据"""
        company = company_service.get_by_code(db, stock_code)
        index_result = index_result_repository.get_by_company_year(db, company.id, year)
        data = evaluation_service.get_with_evidence(db, stock_code, year)
        evaluation = data["evaluation"]
        evidence_by_dim: dict[str, list] = {}
        for ev in data["evidence"]:
            evidence_by_dim.setdefault(ev.dimension_code or "D1", []).append(ev)
        return {
            "company": company, "year": year,
            "index_result": index_result, "evaluation": evaluation,
            "evidence_by_dim": evidence_by_dim, "generated_at": datetime.now(),
        }

    def render_html(self, db: Session, stock_code: str, year: int) -> str:
        data = self.build_report_data(db, stock_code, year)
        c, idx, ev = data["company"], data["index_result"], data["evaluation"]
        dim_rows = "".join(
            f"<tr><td>{DIM_NAMES[d]}</td><td>{getattr(idx, f'{d.lower()}_score') or '-'} </td>"
            f"<td>{(getattr(ev, f'{d.lower()}_evaluation') or '').replace(chr(10), '<br>')}</td></tr>"
            for d in ("D1", "D2", "D3", "D4")
        )
        evidence_rows = "".join(
            f"<li>【{DIM_NAMES.get(d, d)}】《{e.regulation_title}》（{e.regulation_source or ''}）"
            f"相似度 {e.similarity:.2f}</li>"
            for d, items in data["evidence_by_dim"].items() for e in items
        )
        return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>主体自律评价报告</title>
<style>
body {{ font-family: "SimSun", serif; max-width: 800px; margin: 40px auto; line-height: 1.8; }}
h1, h2 {{ text-align: center; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
td, th {{ border: 1px solid #333; padding: 8px; font-size: 14px; }}
.score {{ font-size: 28px; font-weight: bold; text-align: center; }}
</style></head><body>
<h1>上市公司主体自律评价报告</h1>
<p style="text-align:center">生成时间：{data['generated_at']:%Y-%m-%d %H:%M}</p>
<h2>一、公司基本信息</h2>
<table><tr><td>股票代码</td><td>{c.stock_code}</td><td>股票简称</td><td>{c.stock_name}</td></tr>
<tr><td>所属行业</td><td>{c.industry or '-'}</td><td>上市板块</td><td>{c.market or '-'}</td></tr></table>
<h2>二、主体自律指数</h2>
<p class="score">{idx.score if idx else '未计算'} 分（{idx.level if idx else '-'} 级）</p>
<h2>三、多维度评价</h2>
<table><tr><th>维度</th><th>维度得分</th><th>评价意见</th></tr>{dim_rows}</table>
<h2>四、总体评价摘要</h2>
<p>{(ev.overall_summary or '').replace(chr(10), '<br>')}</p>
<h2>五、法规依据与证据溯源</h2>
<ul>{evidence_rows}</ul>
</body></html>"""

    def render_pdf(self, db: Session, stock_code: str, year: int) -> bytes:
        """基于 reportlab 导出 PDF 报告"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        try:
            pdfmetrics.registerFont(TTFont("SimSun", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))
            font = "SimSun"
        except Exception:
            font = "Helvetica"  # 无中文字体环境的兜底
        data = self.build_report_data(db, stock_code, year)
        c, idx, ev = data["company"], data["index_result"], data["evaluation"]

        buf = io.BytesIO()
        cv = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 20 * mm

        def line(text: str, size: int = 11, gap: int = 7):
            nonlocal y
            if y < 20 * mm:
                cv.showPage()
                y = height - 20 * mm
            cv.setFont(font, size)
            cv.drawString(20 * mm, y, text[:80])
            y -= gap * mm

        line("上市公司主体自律评价报告", 18, 12)
        line(f"公司：{c.stock_name}（{c.stock_code}）  年度：{year}", 12, 9)
        line(f"主体自律指数：{idx.score if idx else '未计算'} 分（{idx.level if idx else '-'} 级）", 13, 9)
        for d in ("D1", "D2", "D3", "D4"):
            line(f"{DIM_NAMES[d]}：{getattr(idx, f'{d.lower()}_score') if idx else '-'} 分", 12, 6)
            text = (getattr(ev, f"{d.lower()}_evaluation") or "无") .replace("\n", " ")
            for i in range(0, min(len(text), 400), 40):
                line(text[i:i + 40], 10, 5)
        line("总体摘要：" + (ev.overall_summary or "").replace("\n", " ")[:200], 11, 8)
        cv.save()
        buf.seek(0)
        return buf.read()


report_service = ReportService()
