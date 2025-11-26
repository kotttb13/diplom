from typing import List, Optional, Dict
from datetime import datetime
import logging

from core.database.models.device import Device
from core.repositories.device_repository import DeviceRepository

class DeviceRegisteringService:
    def __init__(self, device_repository: DeviceRepository):
        self.device_repo = device_repository
        self.logger = logging.getLogger(__name__)

    def add_device(self, name: str, ip_address: str, device_type: str, 
                architecture: str, memory_gb: float, processor: str = "", )-> Device:
        device = Device(
            name=name,
            ip_address=ip_address,
            type=device_type,
            architecture=architecture,
            memory=memory_gb,
            processor=processor,
            
        )
        
        self.device_repo.save(device)
        self.logger.info(f"Устройство добавлено: {name} ({ip_address})")
        return device

    def connect_device(self, device_id: str) -> bool:
        device = self.device_repo.get_by_id(device_id)
        if device:
            device.last_seen = datetime.now()
            self.device_repo.save(device)
            self.logger.info(f"Устройство подключено: {device.name}")    
            return True
        return False
        
    def get_all_devices(self) -> List[Device]:
        return self.device_repo.get_all()

    def get_connected_devices(self) -> List[Device]:
        return self.device_repo.get_connected()

    def get_devices_by_id(self, device_id: str) -> List[Device]:
        return self.device_repo.get_by_id(device_id)

