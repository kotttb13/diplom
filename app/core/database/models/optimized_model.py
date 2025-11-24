from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.base import Base
 
class OptimizedModel(Base):
    __tablename__ = "optimized_model" 
    
    id = Column(Integer, primary_key=True)
    original_model_id = Column(Integer, ForeignKey("neural_model.id")) 
    device_id = Column(Integer, ForeignKey("device.id"))  
    path = Column(String, nullable=False) 
    size = Column(Float) 
    optimization_params = Column(Text) 
    
    neural_model_optimized_model = relationship("NeuralModel", back_populates="optimized_model_neural_model")
    record_optimized_model = relationship("OptimizationRecord", back_populates="optimized_model_record")
    deployment_record_optimized_model = relationship("DeploymentRecord", back_populates="optimized_model_deployment_record")
    device_optimized_model = relationship("Device", back_populates="optimized_model_device")

   
    def __repr__(self):
        return f"<OptimizedModel(id={self.id}, size='{self.size}')>"