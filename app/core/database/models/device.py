from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.base import Base
 
class Device(Base):
    __tablename__= "device"

    id = Column(Integer,primary_key=True)
    type = Column(Integer,ForeignKey("device_type.id"))
    name = Column(String, nullable=False)
    ip_address =  Column(String, nullable=False)
    architecture  = Column(String, nullable=False) 
    memory = Column(Float)
    processor = Column(String)
    gpu = Column(Boolean, default=False)

    deployment_record_device = relationship("DeploymentRecord", back_populates="device_deployment_record")
    type_device = relationship("DeviceType", back_populates="device_type")
    optimized_model_device = relationship("OptimizedModel", back_populates="device_optimized_model")

    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', type='{self.type}')>"