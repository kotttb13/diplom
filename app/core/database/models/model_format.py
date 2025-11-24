from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.base import Base
 
class ModelFormat(Base):
    __tablename__ = "model_format" 
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
   
    neural_model_format = relationship("NeuralModel", back_populates="format_neural_model")
 
    def __repr__(self):
        return f"<ModelFormat(id={self.id}, name='{self.name}')>"