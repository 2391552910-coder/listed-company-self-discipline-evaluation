"""
数据导入服务（5.4.1）：CSMAR 结构化指标数据批量导入

支持 Excel/CSV，列格式：stock_code, indicator_code, year, raw_value
"""
import io

import pandas as pd
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.indicator import IndicatorValue
from app.repositories.company_repository import company_repository
from app.repositories.indicator_repository import indicator_repository, indicator_value_repository
from app.services.index_service import init_indicator_system


class ImportService:
    def import_indicator_file(self, db: Session, file_bytes: bytes, filename: str) -> dict:
        """解析上传的 CSMAR 数据文件并批量入库（幂等：同公司+指标+年度覆盖）"""
        init_indicator_system(db)
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            raise BusinessException(f"文件解析失败：{e}")

        required = {"stock_code", "indicator_code", "year", "raw_value"}
        if not required.issubset(df.columns):
            raise BusinessException(f"文件缺少必要列 {required}，当前列为 {list(df.columns)}")

        inserted, skipped = 0, 0
        objs = []
        for _, row in df.iterrows():
            company = company_repository.get_by_code(db, str(row["stock_code"]))
            indicator = indicator_repository.get_by_code(db, str(row["indicator_code"]))
            if not company or not indicator:
                skipped += 1
                continue
            existing = db.query(IndicatorValue).filter(
                IndicatorValue.company_id == company.id,
                IndicatorValue.indicator_id == indicator.id,
                IndicatorValue.year == int(row["year"]),
            ).first()
            if existing:
                existing.raw_value = float(row["raw_value"])
                continue
            objs.append(IndicatorValue(
                company_id=company.id, indicator_id=indicator.id,
                year=int(row["year"]), raw_value=float(row["raw_value"]),
            ))
            inserted += 1
        if objs:
            indicator_value_repository.bulk_create(db, objs)
        db.commit()
        return {"inserted": inserted, "updated": df.shape[0] - inserted - skipped, "skipped": skipped}


import_service = ImportService()
