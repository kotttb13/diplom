from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base
 
class NeuralModel(Base):
    __tablename__ = "neural_model" 
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    format_id = Column(Integer,ForeignKey("model_format.id"))
    type_id = Column(Integer,ForeignKey("model_type.id"))
    size = Column(Float)
     
    optimized_model_neural_model = relationship("OptimizedModel", back_populates="neural_model_optimized_model")
    format_neural_model =  relationship("ModelFormat", back_populates="neural_model_format")
    type_neural_model =  relationship("ModelType", back_populates="neural_model_type")
    record_neural_model = relationship("OptimizationRecord", back_populates="neural_model_record")
    def __repr__(self):
        return f"<NeuralModel(id={self.id}, name='{self.name}')>"