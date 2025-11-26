from abc import ABC, abstractmethod
from typing import Dict, Optional
import paramiko
import logging

class BaseDeviceManager(ABC):
    
    def __init__(self):
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def connect(self, host: str, username: str, password: str, port: int) -> bool:
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict:
        pass
    
    @abstractmethod
    def execute_command(self, command: str, timeout: int = 30) -> Dict:
        pass
    @abstractmethod
    def deploy_file(self, local_path: str, remote_path: str = "~/") -> Dict:
        pass

    def disconnect(self):
        self.logger.debug(f"Закрытие соединения с устройством")
        if self.connection:
            self.connection.close()
            self.connection = None
        self.logger.info(f"Соединение с усройством закрыто")
