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