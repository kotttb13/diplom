
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

    def get_id_by_ip(self, device_ip: str) -> Optional[Device]:
        device_type_obj = self.session.query(Device).filter(Device.ip_address == device_ip).first()
        if device_type_obj:
            return device_type_obj.id
        return -1
    
    def get_by_ip(self, device_ip: str) -> Optional[Device]:
        return self.session.query(Device).filter(Device.ip_address == device_ip).first()
    
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

    def create_device(self, ip_address: str, architecture: str, ram_gb: float, 
                cpu_core: int, device_type: str, memory_gb: float = None, 
                status: str = "active") -> Device:  # Изменили type на device_type

        try:
            device_type_id = self.get_device_type_id(device_type)  # Используем device_type
            if device_type_id == -1:
                device_type_obj = DeviceType(name=device_type)  # Используем device_type
                self.session.add(device_type_obj)
                self.session.flush()  
                device_type_id = device_type_obj.id
            
            device = Device(
                ip_address=ip_address,
                architecture=architecture,
                ram_gb=ram_gb,
                cpu_core=cpu_core,
                memory_gb=memory_gb,
                type_id=device_type_id, 
                last_seen=datetime.now()
            )
            
            self.session.add(device)
            self.session.commit()
            return device
        except Exception as e:
            self.session.rollback()
            raise e