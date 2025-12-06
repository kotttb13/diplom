from typing import List, Optional
from sqlalchemy.orm import Session
from core.database.models import OptimizedModel
from sqlalchemy import desc, and_

class OptimizedModelRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, optimized_model: OptimizedModel) -> None:
        self.session.add(optimized_model)
        self.session.commit()
    
    def get_by_id(self, optimized_model_id: int) -> Optional[OptimizedModel]:
        return self.session.query(OptimizedModel).filter(OptimizedModel.id == optimized_model_id).first()
    
    def get_by_original_model(self, original_model_id: int) -> List[OptimizedModel]:
        return (self.session.query(OptimizedModel)
                .filter(OptimizedModel.original_model_id == original_model_id)
                .all())
    
    def delete(self, optimized_model: OptimizedModel) -> None:
        self.session.delete(optimized_model)
        self.session.commit()


    def get_all(self) -> List[OptimizedModel]:
        return self.session.query(OptimizedModel).order_by(
            desc(OptimizedModel.id)
        ).all()