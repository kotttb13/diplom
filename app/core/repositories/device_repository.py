
from typing import List, Optional
from sqlalchemy.orm import Session


from core.database.models import Device, DeviceType
from datetime import datetime, timedelta 
class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, device: Device) -> None:
        try:
            self.session.add(device)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
    
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

    def get_device_type_id(self, device_type: str) -> Optional[int]:
        normalized = (device_type or "").strip().lower()
        if not normalized:
            return None

        aliases = {
            "raspberry": "raspberry_pi",
            "rpi": "raspberry_pi",
            "ubuntu": "linux",
            "android_like": "android",
        }
        normalized = aliases.get(normalized, normalized)

        device_type_obj = self.session.query(DeviceType).filter(DeviceType.name == normalized).first()
        if device_type_obj:
            return device_type_obj.id
        return None

    def get_or_create_device_type_id(self, device_type: str) -> int:
        existing_id = self.get_device_type_id(device_type)
        if existing_id is not None:
            return existing_id

        normalized = (device_type or "linux").strip().lower() or "linux"
        device_type_obj = DeviceType(name=normalized)
        self.session.add(device_type_obj)
        self.session.flush()
        return device_type_obj.id



    def delete(self, device: Device) -> None:
        self.session.delete(device)
        self.session.commit()

    def create_device(self, ip_address: str, architecture: str, ram_gb: float, 
                cpu_core: int, device_type: str, memory_gb: float = None,
                username: str = None, password: str = None, port: int = None,
                status: str = "active") -> Device:  # Изменили type на device_type

        try:
            device_type_id = self.get_or_create_device_type_id(device_type)
            
            device = Device(
                ip_address=ip_address,
                architecture=architecture,
                ram_gb=ram_gb,
                cpu_core=cpu_core,
                memory_gb=memory_gb,
                device_type=device_type,
                username=username,
                password=password,
                port=port,
                type_id=device_type_id, 
                last_seen=datetime.now()
            )
            
            self.session.add(device)
            self.session.commit()
            return device
        except Exception as e:
            self.session.rollback()
            raise e