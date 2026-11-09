import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import ctypes
import string
import utils
from utils import get_parent_path, is_hidden_windows_file, validate_windows_path


def get_current_drive() -> str:
    """Получение текущего диска Windows"""
    current_path = os.getcwd()
    drive, _ = os.path.splitdrive(current_path)
    return drive

def list_available_drives() -> List[str]:
    """Получение списка доступных дисков Windows"""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1

    return drives

def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Отображение содержимого каталога в Windows"""
    results = []
    file_names = utils.safe_windows_listdir(path)
    for file_name in file_names:
        dict_of_results = {
            "name": file_name,
            'type': 'Unknown',
            'size': 0,
            'modified': 'Unknown',
            'hidden': 'Unknown',
        }

        full_path = os.path.join(path, file_name)
        if os.path.isdir(full_path):
            dict_of_results['type'] = 'directory'
        if os.path.isfile(full_path):
            dict_of_results['type'] = 'file'
        if utils.is_hidden_windows_file(full_path):
            dict_of_results['hidden'] = True
        else:
            dict_of_results['hidden'] = False

        try:
            os_stat = os.stat(full_path)
            dict_of_results['size'] = os_stat.st_size
            dict_of_results['modified'] = datetime.fromtimestamp(os_stat.st_mtime).strftime('%Y-%m-%d')


        except (FileNotFoundError, PermissionError, OSError):
            pass
        results.append(dict_of_results)
    return True, results

def format_directory_output(items: List[Dict[str, Any]]) -> None:
    """Форматированный вывод содержимого каталога для Windows"""
    print(f"{'Имя':<30} | {'Тип':<10} | {'Размер':>10} | {'Изменен':<12} | {'Скрытый'}")
    print("-" * 80)

    for item in items:
        size_str = utils.format_size(item['size'])
        hidden_str = "[скрыт]" if item['hidden'] else ""
        print(f"{item['name']:<30} | {item['type']:<10} | {size_str:>10} | {item['modified']:<12} | {hidden_str}")

def move_up(current_path: str) -> str:
    """Переход в родительский каталог в Windows"""
    parent_path = utils.get_parent_path(current_path)
    if utils.validate_windows_path(parent_path)[0]:
        return parent_path
    else:
        return current_path

def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    """Переход в указанный подкаталог в Windows"""

    if target_dir in utils.safe_windows_listdir(current_path):
        new_path = os.path.join(current_path, target_dir)
        if utils.validate_windows_path(new_path)[0]:
            return True, new_path
        else:
            return False, current_path
    else:
        return False, current_path

def get_windows_special_folders() -> Dict[str, str]:
    """Получение путей к специальным папкам Windows"""

    path = os.environ.get('USERPROFILE')
    if path:
        return {
            "Desktop": os.path.join(path, "Desktop"),
            "Documents": os.path.join(path, "Documents"),
            "Downloads": os.path.join(path, "Downloads")
        }
    else:
        return {}







