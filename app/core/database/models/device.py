from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base
 
class Device(Base):
    __tablename__= "device"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer,primary_key=True)
    type = Column(Integer,ForeignKey("device_type.id"))
    ip_address =  Column(String, nullable=False)
    architecture  = Column(String, nullable=False) 
    memory_gb = Column(Float)
    ram_gb = Column(Float)
    cpu_core = Column(Integer)
    last_seen =  Column(DateTime, default=datetime.utcnow)

    deployment_record_device = relationship("DeploymentRecord", back_populates="device_deployment_record")
    type_device = relationship("DeviceType", back_populates="device_type")
    optimized_model_device = relationship("OptimizedModel", back_populates="device_optimized_model")

    def __repr__(self):
        return f"<Device(id={self.id}, ip='{self.ip_address}', type='{self.type}')>"