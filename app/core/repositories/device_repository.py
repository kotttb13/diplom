
from typing import List, Optional
from sqlalchemy.orm import Session

from core.database.models.device import Device
from datetime import datetime, timedelta 
class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, device: Device) -> None:
        self.session.add(device)
        self.session.commit()
    
    def get_by_id(self, device_id: str) -> Optional[Device]:
        return self.session.query(Device).filter(Device.id == device_id).first()
    
    def get_all(self) -> List[Device]:
        return self.session.query(Device).all()
    
    def get_connected(self) -> List[Device]:
        five_min_ago = datetime.now() - timedelta(minutes=5)
        return self.session.query(Device).filter(
            Device.last_seen >= five_min_ago
        ).all()

        
    def delete(self, device: Device) -> None:
        self.session.delete(device)
        self.session.commit()
