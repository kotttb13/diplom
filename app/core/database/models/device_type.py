from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.base import Base
  
class DeviceType(Base):
    __tablename__ = "device_type" 
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
   
    device_type = relationship("Device", back_populates="type_device")
 
    def __repr__(self):
        return f"<DeviceType(id={self.id}, name='{self.name}')>"