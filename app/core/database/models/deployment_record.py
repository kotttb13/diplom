from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.base import Base
 
class DeploymentRecord(Base):
    __tablename__ = "deployment_record" 
    
    id = Column(Integer, primary_key=True)
    optimized_model_id = Column(Integer, ForeignKey("optimized_model.id")) 
    device_id = Column(Integer, ForeignKey("device.id"))  
    deployment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False) 
    
    
    optimized_model_deployment_record = relationship("OptimizedModel", back_populates="deployment_record_optimized_model")
    device_deployment_record = relationship("Device", back_populates="deployment_record_device")
    
    def __repr__(self):
        return f"<DeploymentRecord(id={self.id}, status='{self.status}')>"