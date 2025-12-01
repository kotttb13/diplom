from .android_device_manager import AndroidDeviceManager
from .device_registering_service import DeviceRegisteringService
from typing import List, Optional, Dict


class UniversalDeviceService:

    def __init__(self, device_repository):

        self.device_manager = None
        self._current_device_info = None
        self.registering = DeviceRegisteringService(device_repository)  
    def get_manager(self, device_type: str):
        managers = {
            'android': AndroidDeviceManager
        }
        
        if device_type not in managers:
            return 'error'
        return managers[device_type]



    def connect_device(self, device_type: str, **connection_params) -> Dict:
        try:
            manager = self.get_manager(device_type)
            if manager == "error":
                return  {'success':  False, 'error': f'Неизвестный тип устройства: {device_type}'}
            self.device_manager = manager()

            success = self.device_manager.connect(**connection_params)
            
            if success:
                return {
                    'success': True,
                    'message': f'Успешное подключение к {device_type}'
                }
            else:
                return {'success': False, 'error': 'Не удалось подключиться'}
        except Exception as e:
             return {'success': False, 'error': e}


    def get_and_save_device_info(self) -> Dict:
        try:
        
            if self.device_manager == None:
                return  {'success': False, 'error': "нет подключения"}
            info = self.device_manager.get_device_info()
            print(info)
            if info:

                self.registering.add_device(ip_address=info["ip_address"], device_type=info["type"], 
                architecture=info["architecture"], memory_gb=info["memory_gb"], ram_gb=info["ram_gb"], cpu_core=info["cpu_core"], last_seen=info["last_seen"])
                return {'success': True, 'message': info}
        except Exception as e:
             return {'success': False, 'error': e}




        