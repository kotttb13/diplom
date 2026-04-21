from typing import List, Optional, Dict
from datetime import datetime
import logging

from core.database.models import Device

from core.repositories.device_repository import DeviceRepository

class DeviceRegisteringService:
    def __init__(self, device_repository: DeviceRepository):
        self.device_repo = device_repository
        self.logger = logging.getLogger(__name__)

    def add_device(self, ip_address: str, device_type: str,
                architecture: str, memory_gb: float, ram_gb: float, cpu_core: int, last_seen,
                device_type_actual: str = None, cpu_frequency: int = None, gpu_memory: int = None )-> Device:
        device_type_id = self.device_repo.get_or_create_device_type_id(device_type)
        device = Device(
        
            ip_address=ip_address,
            type_id=device_type_id,
            architecture=architecture,
            memory_gb = memory_gb,
            ram_gb = ram_gb,
            cpu_core = cpu_core,
            device_type=device_type_actual or device_type,
            cpu_frequency=cpu_frequency,
            gpu_memory=gpu_memory,
            last_seen =  last_seen
            
        )
        
        self.device_repo.save(device)
        print(f"Устройство добавлено: {ip_address}")
        self.logger.info(f"Устройство добавлено:{ip_address}")
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

    def get_devices_by_id(self, device_id: int) -> List[Device]:
        return self.device_repo.get_by_id(device_id)

    def get_devices_by_ip(self, device_ip: str) -> Device:
        return self.device_repo.get_id_by_ip(device_ip)
    
    def get_device_type_id(self, device_type: str) -> int:
        return self.device_repo.get_device_type_id(device_type)

