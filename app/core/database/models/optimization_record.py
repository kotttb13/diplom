from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base
 
class OptimizationRecord(Base):
    __tablename__ = "optimization_record" 
    
    id = Column(Integer, primary_key=True)
    optimized_model_id = Column(Integer, ForeignKey("optimized_model.id"))
    original_model_id = Column(Integer, ForeignKey('neural_model.id'))
    accuracy_before = Column(Float)
    accuracy_after = Column(Float)
    loss_before = Column(Float)
    loss_after = Column(Float)
    status = Column(String, nullable=False)
    
    neural_model_record = relationship("NeuralModel", back_populates="record_neural_model")
    optimized_model_record = relationship("OptimizedModel", back_populates="record_optimized_model")
    
    def __repr__(self):
        return f"<OptimizationRecord(id={self.id}, status='{self.status}')>"