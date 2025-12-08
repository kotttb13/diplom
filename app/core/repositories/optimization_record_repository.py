from typing import List, Optional
from sqlalchemy.orm import Session
from core.database.models import OptimizationRecord

class OptimizationRecordRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, record: OptimizationRecord) -> None:
        self.session.add(record)
        self.session.commit()
    
    def get_by_id(self, record_id: int) -> Optional[OptimizationRecord]:
        return self.session.query(OptimizationRecord).filter(OptimizationRecord.id == record_id).first()
    
    def get_by_optimized_model(self, optimized_model_id: int) -> List[OptimizationRecord]:
        return (self.session.query(OptimizationRecord)
                .filter(OptimizationRecord.optimized_model_id == optimized_model_id)
                .all())
    def get_recent_records(self, limit=10) -> List[OptimizationRecord]:
        return self.session.query(OptimizationRecord).order_by(OptimizationRecord.id.desc()).limit(limit).all()
    
    def get_all(self):
        return self.session.query(OptimizationRecord).all()
    
    def delete(self, record: OptimizationRecord) -> None:
        self.session.delete(record)
        self.session.commit()