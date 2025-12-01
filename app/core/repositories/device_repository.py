
from typing import List, Optional
from sqlalchemy.orm import Session


from core.database.models import Device, DeviceType
from datetime import datetime, timedelta 
class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, device: Device) -> None:
        self.session.add(device)
        self.session.commit()
    
    def get_by_id(self, device_id: int) -> Optional[Device]:
        return self.session.query(Device).filter(Device.id == device_id).first()

    def get_by_ip(self, device_ip: str) -> Optional[Device]:
        device_type_obj = self.session.query(Device).filter(Device.ip == device_ip).first()
        if device_type_obj:
            return device_type_obj.id
        return -1
    
    def get_all(self) -> List[Device]:
        return self.session.query(Device).all()
    
    def get_connected(self) -> List[Device]:
        five_min_ago = datetime.now() - timedelta(minutes=5)
        return self.session.query(Device).filter(
            Device.last_seen >= five_min_ago
        ).all()

    def get_device_type_id (self, device_type):
        device_type_obj = self.session.query(DeviceType).filter(DeviceType.name == device_type).first()
        if device_type_obj:
            return device_type_obj.id
        return -1



    def delete(self, device: Device) -> None:
        self.session.delete(device)
        self.session.commit()
