import paramiko
import socket
import time
import json
from typing import Dict, Optional
import logging
import os
import subprocess
from .base_device_manager import BaseDeviceManager

class AndroidDeviceManager(BaseDeviceManager):
    def __init__(self):
        self.ip = None
        self.connection = None
        self.logger = logging.getLogger(__name__)

    
    def connect(self, host: str, username: str, password: str, port: int = 8022) -> bool:
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.logger.debug(f"Попытка подключения к устройству  {username}@{host}:{port} ")
            self.ip = host
            client.connect(
                hostname=host,
                username=username,
                password=password,
                port=port,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            stdin, stdout, stderr = client.exec_command("echo 'SUCCESS' && pwd")
            output = stdout.read().decode().strip()
            
            if "SUCCESS" in output:
                self.connection = client
                self.logger.info(f"Успешное подключение к Android!")
                return True
            else:
                self.logger.debug(f"К устройству Android подключиться не получилось")
                client.close()
                return False
                
        except paramiko.AuthenticationException:
            self.logger.error(f"Ошибка аунтификации! Проверьте имя пользователя и пароль")
            return False
        except paramiko.SSHException as e:
            self.logger.error(f"Ошибка ssh:{e}")
            return False
        except socket.timeout:
            self.logger.error(f"Таймаут подключения. Проверьте:\n- Что устройства в одной Wi-Fi сети\n- Что IP адрес правильный\n- Что Termux работает и SSH сервер запущен")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка:{e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict:
        
        if not self.connection:
            self.logger.error(f"Не удалось выполнить команду, поскольку нет подключения к устройству!")
            return {'error': 'Нет подключения к Android'}
        
        try:
            self.logger.debug(f"Выполнение команды {command}")
            stdin, stdout, stderr = self.connection.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()
            
            result = {
                'exit_status': exit_status,
                'output': output,
                'error': error,
                'success': exit_status == 0
            }
            
            if error and not output:
                self.logger.error(f"Команда завершилась с ошибкой: {error}")
            elif output:
                self.logger.info(f"Команда завершилась успешно!")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Возникла ошибка при выполнении команды: {e}")
            return {'error': f'Ошибка выполнения: {e}', 'success': False}
    
    
    def get_free_memory(self)->Dict:
        self.logger.debug(f"Получение информации о свободной памяти Android устройства")
        info = dict()
        if not self.connection:
            self.logger.error(f"Не удалось выполнить команду, поскольку нет подключения к устройству!")
            return {'error': 'Нет подключения', 'success': False}
        command = "df -h /data | awk \'NR==2{print $4}\' | sed \'s/G//\'"
        result = self.execute_command(command)
        if result['success'] and result['output']:
            print("Значение свободной памяти получено!")
            self.logger.info(f"Значение свободной памяти получено!")
            info["memory_gb"] = result['output']
        else:
            print("Значение свободной памяти не удалось получить!")
            self.logger.info(f"Значение свободной памяти не удалось получить!")
            info =  {'error': 'Unknown error', 'success': False}
        return info

    def get_device_info(self) -> Dict:
        self.logger.debug(f"Получение подробной информации об Android устройстве")
        if not self.connection:
            self.logger.error(f"Не удалось выполнить команду, поскольку нет подключения к устройству!")
            return {'error': 'Нет подключения', 'success': False}
        
        info = {
            'last_seen': time.strftime('%Y-%m-%d %H:%M:%S'),
            'type_device': "android",
            "ip_address": self.ip,
            "cpu_frequency": None,
            "gpu_memory": None,
        }
        
        commands = {
            'architecture': 'uname -m',
            'memory_gb': 'df -h /data | awk \'NR==2{print $4}\' | sed \'s/G//\'',
            'ram_gb': 'awk \'/MemTotal/ {print int($2/1024/1024)}\' /proc/meminfo',
            'cpu_core': 'nproc 2>/dev/null || -1',
            }
        
        for key, command in commands.items():
            self.logger.debug(f"Получение {key}")
            result = self.execute_command(command)
            if result['success'] and result['output']:
                self.logger.info(f"{key} получено!")
                info[key] = result['output']
            else:
                self.logger.info(f"{key} не удалось получить!")
                info[key] = f"Не доступно: {result.get('error', 'Unknown error')}"
            time.sleep(0.1)  
        
        return info

    def install_dependencies(self) -> Dict:
        cmd = "pkg update -y && pkg install -y python python-numpy && pip install onnxruntime tflite-runtime"
        return self.execute_command(cmd, timeout=300)
    
    def deploy_file(self, local_path: str, remote_path: str = "~/") -> Dict:
        if not self.connection:
            return {'success': False, 'error': 'Нет SSH подключения'}
        
        try:
            remote_path_fixed = remote_path
            if remote_path.startswith("~/"):
                result = self.execute_command("pwd")
                if result.get('success'):
                    home_dir = result.get('output', '').strip()
                    remote_path_fixed = remote_path.replace("~/", f"{home_dir}/")
                else:
                    remote_path_fixed = remote_path.replace("~/", "/data/data/com.termux/files/home/")
            
            remote_dir = os.path.dirname(remote_path_fixed)
            if remote_dir:
                mkdir_cmd = f'mkdir -p "{remote_dir}"'
                self.execute_command(mkdir_cmd)
            
            with self.connection.open_sftp() as sftp:
                sftp.put(local_path, remote_path_fixed)
            
            check_cmd = f'ls -la "{remote_path_fixed}"'
            result = self.execute_command(check_cmd)
            
            if 'No such file' not in result.get('output', ''):
                return {
                    'success': True,
                    'message': f'Файл загружен',
                    'remote_path': remote_path,  # Возвращаем оригинальный путь
                    'actual_path': remote_path_fixed  # И фактический путь
                }
            else:
                return {
                    'success': False,
                    'error': f'Файл не загружен: {remote_path_fixed}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'SFTP ошибка: {str(e)}'}
        


    def create_decrypt_command(self, encrypted_path: str, output_path: str,
                          checksum_path: str, device_id: str, secret: str) -> str:

        cmd = f'''cd ~ && python3 -c "
import base64, hashlib, os
from cryptography.fernet import Fernet


enc = '{encrypted_path}'
out = '{output_path}'
dev_id = '{device_id}'
sec = '{secret}'


key = base64.urlsafe_b64encode(
        hashlib.pbkdf2_hmac('sha256', sec.encode(), dev_id.encode(), 100000, 32)
)


with open(enc, 'rb') as f:
    data = Fernet(key).decrypt(f.read())

with open(out, 'wb') as f:
    f.write(data)

print('done')
    "
    '''
        return cmd
