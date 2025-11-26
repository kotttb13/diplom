from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from core.database.base import Base
  
class DeviceType(Base):
    __tablename__ = "device_type" 
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
   
    device_type = relationship("Device", back_populates="type_device")
 
    def __repr__(self):
        return f"<DeviceType(id={self.id}, name='{self.name}')>"