import paramiko
import socket
import time
import json
from typing import Dict, Optional
import logging
import os
from scp import SCPClient
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
    
    def get_device_info(self) -> Dict:
        self.logger.debug(f"Получение подробной информации об Android устройстве")
        if not self.connection:
            self.logger.error(f"Не удалось выполнить команду, поскольку нет подключения к устройству!")
            return {'error': 'Нет подключения', 'success': False}
        
        info = {
            'last_seen': time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': "Mobile",
            "ip_address": self.ip
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
    
    def deploy_file(self, local_path: str, remote_path: str = "~/") -> Dict:
        self.logger.debug(f"Загрузка файлов на устройство") 
        if not self.connection:
            self.logger.error(f"Не удалось выполнить команду, поскольку нет подключения к устройству!")
            return {'error': 'Нет подключения', 'success': False}
        
        try:
            if not os.path.exists(local_path):
                self.logger.error(f"Не удалось найти путь к файлу для развертывания!")
                return {'error': f'Локальный файл {local_path} не существует'}
            
            filename = os.path.basename(local_path)
            full_remote_path = f"{remote_path.rstrip('/')}/{filename}"
            
            
            with SCPClient(self.connection.get_transport()) as scp:
                scp.put(local_path, full_remote_path)
            

            result = self.execute_command(f"ls -la {full_remote_path}")
            if result['success']:
                self.logger.info(f"Файл успешно загружен на устройство!")
                file_info = result['output'].split()
                return {
                    'success': True,
                    'message': 'Файл успешно загружен',
                    'remote_path': full_remote_path,
                    'file_size': file_info[4] if len(file_info) > 4 else 'unknown',
                    'permissions': file_info[0] if len(file_info) > 0 else 'unknown'
                }
            else:
                self.logger.error('Не удалось подтвердить загрузку файла')
                return {'error': 'Не удалось подтвердить загрузку файла'}
                
        except ImportError:
            self.logger.error("Ошибка! Модуль scp не установлен")
            return {'error': 'Модуль scp не установлен. Установите: pip install scp'}
        except Exception as e:
            self.logger.error(f"Ошибка загрузки: {e}")
            return {'error': f'Ошибка загрузки: {e}', 'success': False}
    
    def disconnect(self):
        try:
            self.logger.debug(f"Закрытие соединения с устройством")
            if self.connection:
                self.connection.close()
                self.connection = None
            self.logger.info(f"Соединение с усройством закрыто")
            return True
        except Exception as e:
            return False
    


