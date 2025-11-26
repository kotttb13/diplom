from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from core.database.base import Base

 
class Device(Base):
    __tablename__= "device"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer,primary_key=True)
    type = Column(Integer,ForeignKey("device_type.id"))
    ip_address =  Column(String, nullable=False)
    architecture  = Column(String, nullable=False) 
    memory = Column(Float)
    cpu_cores = Column(Integer)
    last_seen =  Column(DateTime, default=datetime.utcnow)

    deployment_record_device = relationship("DeploymentRecord", back_populates="device_deployment_record")
    type_device = relationship("DeviceType", back_populates="device_type")
    optimized_model_device = relationship("OptimizedModel", back_populates="device_optimized_model")

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', type='{self.type}')>"