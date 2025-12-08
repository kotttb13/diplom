from .android_device_manager import AndroidDeviceManager
from .device_registering_service import DeviceRegisteringService
from typing import List, Optional, Dict
import tempfile
import os
import hashlib
from cryptography.fernet import Fernet
import base64
import json

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
                    'message': f'Успешное подключение к {device_type}',
                    'manager': self.device_manager
                }
            else:
                return {'success': False, 'error': 'Не удалось подключиться'}
        except Exception as e:
             return {'success': False, 'error': e}

    
    def get_free_memory(self)->Dict:
        try:
        
            if self.device_manager == None:
                return  {'success': False, 'error': "нет подключения"}
            info = self.device_manager.get_free_memory()
            return info
        except Exception as e:
             return {'success': False, 'error': e}

    def get_device_info(self) -> Dict:
        try:
        
            if self.device_manager == None:
                return  {'success': False, 'error': "нет подключения"}
            info = self.device_manager.get_device_info()
            return info
        except Exception as e:
             return {'success': False, 'error': e}

    def get_and_save_device_info(self) -> Dict:
        try:
        
            if self.device_manager == None:
                return  {'success': False, 'error': "нет подключения"}
            info = self.device_manager.get_device_info()
            print(info)
            if info:

                self.registering.add_device(ip_address=info["ip_address"], device_type=info["type_device"], 
                architecture=info["architecture"], memory_gb=info["memory_gb"], ram_gb=info["ram_gb"], cpu_core=info["cpu_core"], last_seen=info["last_seen"])
                return {'success': True, 'message': info}
        except Exception as e:
             return {'success': False, 'error': e}


    def deploy_ota_update(self, 
                         model_path: str,
                         model_id: int,
                         device_id: int,
                         secret: str = None, 
                         remote_dir: str = "~/ota_updates/") -> Dict:
        original_ext = os.path.splitext(model_path)[1]
        original_ext = original_ext.lstrip('.')
        if not self.device_manager:
            return {'success': False, 'error': 'Сначала подключитесь к устройству'}
        
        try:

            if remote_dir.startswith("~/"):
                # Получаем домашнюю директорию
                result = self.device_manager.execute_command("echo $HOME")
                if result.get('success'):
                    home_dir = result.get('output', '').strip()
                    remote_dir = remote_dir.replace("~/", f"{home_dir}/")
                else:
                    # Fallback для Termux
                    remote_dir = remote_dir.replace("~/", "/data/data/com.termux/files/home/")

            if remote_dir:
                mkdir_cmd = f'mkdir -p "{remote_dir}"'
                self.device_manager.execute_command(mkdir_cmd)


            encrypted_data, checksum = self._encrypt_file_aes(
                model_path, 
                str(device_id), 
                secret or f"ota_{device_id}"
            )
            
            
            with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
                f.write(encrypted_data)
                temp_encrypted_path = f.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.checksum', delete=False) as f:
                f.write(checksum)
                temp_checksum_path = f.name
            
            try:
                remote_encrypted = f"{remote_dir}model_{model_id}.enc"
                remote_checksum = f"{remote_dir}model_{model_id}.checksum"
                remote_output = f"{remote_dir}model_{model_id}.{original_ext}"
                
                result1 = self.device_manager.deploy_file(
                    local_path=temp_encrypted_path,
                    remote_path=remote_encrypted
                )
                
                result2 = self.device_manager.deploy_file(
                    local_path=temp_checksum_path,
                    remote_path=remote_checksum
                )
                
                if result1.get('success') and result2.get('success'):
                    install_cmd = self.install_cryptography_command()
                    install_result = self.device_manager.execute_command(install_cmd)
                    if not install_result.get('success'):
                        return {
                            'success': False,
                            'error': f'Не удалось установить cryptography: {install_result.get("error")}'
                        }
                    decrypt_cmd = self.device_manager.create_decrypt_command(
                        encrypted_path=remote_encrypted,
                        output_path=remote_output,
                        checksum_path=remote_checksum,
                        device_id=str(device_id),
                        secret=secret or f"ota_{device_id}"
                    )
                    
                    cmd_result = self.device_manager.execute_command(decrypt_cmd)
                    
                    if cmd_result.get('success'):
                       
                        cleanup_cmd = f"rm -f {remote_encrypted} {remote_checksum}"
                        self.device_manager.execute_command(cleanup_cmd)
                        
                        return {
                            'success': True,
                            'message': 'OTA обновление успешно развернуто',
                            'output_file': remote_output,
                            'checksum': checksum,
                            'original_size': os.path.getsize(model_path)
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Ошибка дешифрования: {cmd_result.get("error")}'
                        }
                else:
                    errors = []
                    if not result1.get('success'):
                        errors.append(f'Файл: {result1.get("error")}')
                    if not result2.get('success'):
                        errors.append(f'Checksum: {result2.get("error")}')
                    return {'success': False, 'error': '; '.join(errors)}
                    
            finally:
                os.unlink(temp_encrypted_path)
                os.unlink(temp_checksum_path)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    

    def _encrypt_file_aes(self, file_path: str, device_id: str, secret: str):
        key_material = hashlib.pbkdf2_hmac(
            'sha256',
            secret.encode(),
            device_id.encode(),
            100000,  
            32   
        )
        key = base64.urlsafe_b64encode(key_material)
        
        fernet = Fernet(key)
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = fernet.encrypt(file_data)
        checksum = hashlib.sha256(encrypted_data).hexdigest()
        
        return encrypted_data, checksum
    
    def install_cryptography_command(self) -> str:
        """
        Возвращает команду для установки cryptography на устройстве
        """
        return "pkg install python-cryptography -y"