from .android_device_manager import AndroidDeviceManager
from .linux_device_manager import LinuxDeviceManager
from .raspberry_pi_manager import RaspberryPiManager
from .network_scanner import NetworkScanner
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
            'android': AndroidDeviceManager,
            'linux': LinuxDeviceManager,
            'raspberry_pi': RaspberryPiManager,
        }
        
        if device_type not in managers:
            return 'error'
        return managers[device_type]



    def _detect_type_auto(self, **connection_params) -> str:
        test_manager = LinuxDeviceManager()
        if not test_manager.connect(**connection_params):
            return "android"
        # Keep auto-detection responsive; long SSH command timeouts freeze UI.
        probe = test_manager.execute_command("cat /proc/device-tree/model", timeout=3)
        if probe.get("success") and "Raspberry Pi" in probe.get("output", ""):
            test_manager.disconnect()
            return "raspberry_pi"
        probe_snapshot = test_manager.execute_command("devicefs-cat /proc/device-tree/model", timeout=3)
        if probe_snapshot.get("success") and "Raspberry Pi" in probe_snapshot.get("output", ""):
            test_manager.disconnect()
            return "raspberry_pi"
        android_probe = test_manager.execute_command("getprop ro.build.version.release", timeout=3)
        if android_probe.get("success") and android_probe.get("output"):
            test_manager.disconnect()
            return "android"
        test_manager.disconnect()
        return "linux"

    def connect_device(self, device_type: str, **connection_params) -> Dict:
        try:
            if device_type == "auto":
                device_type = self._detect_type_auto(**connection_params)
            manager = self.get_manager(device_type)
            if manager == "error":
                return  {'success':  False, 'error': f'Неизвестный тип устройства: {device_type}'}
            self.device_manager = manager()

            success = self.device_manager.connect(**connection_params)
            
            if success:
                return {
                    'success': True,
                    'message': f'Успешное подключение к {device_type}',
                    'manager': self.device_manager,
                    'device_type': device_type,
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
            if isinstance(info, dict):
                payload = dict(info)
                payload.setdefault("success", True)
                return payload
            return {'success': False, 'error': "Некорректный ответ устройства"}
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
                architecture=info["architecture"], memory_gb=info["memory_gb"], ram_gb=info["ram_gb"], cpu_core=info["cpu_core"], last_seen=info["last_seen"],
                device_type_actual=info.get("type_device"),
                cpu_frequency=info.get("cpu_frequency"), gpu_memory=info.get("gpu_memory"))
                return {'success': True, 'message': info}
        except Exception as e:
             return {'success': False, 'error': e}

    def scan_network(self, username: str = None, password: str = None) -> Dict:
        scanner = NetworkScanner(ssh_ports=[22, 2222, 2223, 8022])
        hosts = scanner.scan_open_ssh_hosts()
        detected = [
            scanner.detect_device_type(
                host=target["host"],
                port=int(target["port"]),
                username=username,
                password=password,
            )
            for target in hosts
        ]
        return {"success": True, "devices": detected}

    def install_dependencies(self, device_type: str) -> Dict:
        if not self.device_manager:
            return {"success": False, "error": "Сначала подключитесь к устройству"}
        if hasattr(self.device_manager, "install_dependencies"):
            return self.device_manager.install_dependencies()
        commands = {
            "android": "pkg update -y && pkg install -y python && pip install numpy onnxruntime",
            "linux": "sudo apt-get update -y && sudo apt-get install -y python3-pip && python3 -m pip install numpy onnxruntime",
        }
        cmd = commands.get(device_type, commands["linux"])
        return self.device_manager.execute_command(cmd, timeout=300)


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
                    remote_dir = remote_dir.replace("~/", "/data/data/com.termux/files/home/")

            if remote_dir:
                mkdir_cmd = f'mkdir -p "{remote_dir}"'
                self.device_manager.execute_command(mkdir_cmd)

            manager_name = self.device_manager.__class__.__name__.lower() if self.device_manager else ""
            is_android_target = "android" in manager_name
            if not is_android_target:
                android_probe = self.device_manager.execute_command(
                    "command -v getprop >/dev/null 2>&1 && echo android || true",
                    timeout=5,
                )
                is_android_target = android_probe.get("success") and "android" in android_probe.get("output", "")
            # Raspberry/Linux targets frequently have restricted package/network access.
            # Avoid hanging on cryptography installation and deploy model directly.
            if not is_android_target:
                remote_output = f"{remote_dir}model_{model_id}.{original_ext}"
                plain_result = self.device_manager.deploy_file(
                    local_path=model_path,
                    remote_path=remote_output
                )
                if plain_result.get('success'):
                    with open(model_path, 'rb') as plain_file:
                        plain_checksum = hashlib.sha256(plain_file.read()).hexdigest()
                    return {
                        'success': True,
                        'message': 'OTA обновление успешно развернуто (без шифрования)',
                        'output_file': remote_output,
                        'checksum': plain_checksum,
                        'original_size': os.path.getsize(model_path),
                    }
                return {'success': False, 'error': f'Ошибка загрузки файла: {plain_result.get("error")}'}


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
                        if is_android_target:
                            self._run_android_crypto_repair()
                            install_result = self.device_manager.execute_command(install_cmd)
                            if not install_result.get('success'):
                                plain_deploy = self.device_manager.deploy_file(
                                    local_path=model_path,
                                    remote_path=remote_output
                                )
                                if plain_deploy.get('success'):
                                    cleanup_cmd = f"rm -f {remote_encrypted} {remote_checksum}"
                                    self.device_manager.execute_command(cleanup_cmd)
                                    return {
                                        'success': True,
                                        'message': 'OTA обновление развернуто без шифрования (fallback)',
                                        'output_file': remote_output,
                                        'checksum': checksum,
                                        'original_size': os.path.getsize(model_path),
                                        'warning': f'Не удалось установить cryptography после auto-fix: {install_result.get("error")}',
                                    }
                        # Fallback for restricted/offline targets: deploy plain model directly.
                        plain_deploy = self.device_manager.deploy_file(
                            local_path=model_path,
                            remote_path=remote_output
                        )
                        if plain_deploy.get('success'):
                            cleanup_cmd = f"rm -f {remote_encrypted} {remote_checksum}"
                            self.device_manager.execute_command(cleanup_cmd)
                            return {
                                'success': True,
                                'message': 'OTA обновление развернуто без шифрования (fallback)',
                                'output_file': remote_output,
                                'checksum': checksum,
                                'original_size': os.path.getsize(model_path),
                                'warning': f'Не удалось установить cryptography: {install_result.get("error")}',
                            }
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
                    if not cmd_result.get('success') and is_android_target:
                        decrypt_error_text = f"{cmd_result.get('error', '')} {cmd_result.get('output', '')}"
                        if any(token in decrypt_error_text for token in ["_cffi_backend", "ModuleNotFoundError", "cryptography"]):
                            self._run_android_crypto_repair()
                            install_result = self.device_manager.execute_command(install_cmd)
                            if install_result.get("success"):
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
                        if is_android_target:
                            plain_deploy = self.device_manager.deploy_file(
                                local_path=model_path,
                                remote_path=remote_output
                            )
                            if plain_deploy.get('success'):
                                cleanup_cmd = f"rm -f {remote_encrypted} {remote_checksum}"
                                self.device_manager.execute_command(cleanup_cmd)
                                return {
                                    'success': True,
                                    'message': 'OTA обновление развернуто без шифрования (fallback)',
                                    'output_file': remote_output,
                                    'checksum': checksum,
                                    'original_size': os.path.getsize(model_path),
                                    'warning': f'Не удалось выполнить дешифрование после auto-fix: {cmd_result.get("error")}',
                                }
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
        # Determine package manager on target device instead of relying on selected type.
        return (
            "python3 -c 'import cryptography' >/dev/null 2>&1 && exit 0; "
            "if command -v pkg >/dev/null 2>&1; then "
            "pkg install -y python-cryptography || python3 -m pip install cryptography; "
            "elif command -v apt-get >/dev/null 2>&1; then "
            "if [ \"$(id -u)\" = \"0\" ]; then "
            "apt-get update -y && (apt-get install -y python3-cryptography || python3 -m pip install --user cryptography || python3 -m pip install cryptography); "
            "elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then "
            "sudo -n apt-get update -y && (sudo -n apt-get install -y python3-cryptography || python3 -m pip install --user cryptography || python3 -m pip install cryptography); "
            "else "
            "python3 -m pip install --user cryptography || pip install --user cryptography; "
            "fi; "
            "elif command -v apk >/dev/null 2>&1; then "
            "if [ \"$(id -u)\" = \"0\" ]; then apk add py3-cryptography || python3 -m pip install cryptography; "
            "elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then sudo -n apk add py3-cryptography || python3 -m pip install --user cryptography; "
            "else python3 -m pip install --user cryptography; fi; "
            "elif command -v dnf >/dev/null 2>&1; then "
            "if [ \"$(id -u)\" = \"0\" ]; then dnf install -y python3-cryptography || python3 -m pip install cryptography; "
            "elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then sudo -n dnf install -y python3-cryptography || python3 -m pip install --user cryptography; "
            "else python3 -m pip install --user cryptography; fi; "
            "else "
            "python3 -m pip install --user cryptography || python3 -m pip install cryptography || pip install --user cryptography; "
            "fi"
        )

    def _android_crypto_repair_commands(self) -> List[str]:
        return [
            "pkg update -y",
            "pkg install -y python rust clang libffi openssl make pkg-config",
            "python3 -m pip install --upgrade pip setuptools wheel",
            "python3 -m pip uninstall -y cryptography cffi || true",
            "python3 -m pip install --no-cache-dir --upgrade cffi",
            "python3 -m pip install --no-cache-dir --upgrade cryptography",
            "python3 -c 'import cffi, cryptography; print(\"crypto-ok\")'",
        ]

    def _run_android_crypto_repair(self) -> List[Dict]:
        if not self.device_manager:
            return []
        results: List[Dict] = []
        for cmd in self._android_crypto_repair_commands():
            results.append(self.device_manager.execute_command(cmd, timeout=300))
        return results
