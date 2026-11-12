import os
import platform
from pathlib import Path
from typing import Union, List, Tuple, Dict, Any
import ctypes

PathString = Union[str, Path]

FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_SYSTEM = 0x04
FILE_ATTRIBUTE_READONLY = 0x01
MAX_DEPTH = 100


def is_windows_os() -> bool:
    """
    Checking that the program is running on Windows
    :return: True if Windows, False otherwise
    """
    return platform.system() == "Windows"

def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Checking the correctness of the Windows path"""
    path = str(path)
    forbidden_chars = '/<>:"|?*'

    if not path:
        return False, "Путь не может быть пустым"

    for index, char in enumerate(path):
        if char in forbidden_chars:
            if char == ":" and index == 1 and path[0].isalpha():
                continue

            return False, "Путь содержит запрещённые символы"

    if len(path) > 260:
        return False, "Путь превышает допустимую длину (260 символов)"

    if not os.path.exists(path):
        return False, "Указанный путь не существует"

    return True, ""

def format_size(size_bytes: int) -> str:
    """
    Formatting the file size in a readable format for Windows
    :return: file size
    """
    if size_bytes <= 0:
        return "0 B"

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size = size_bytes / 1024
    units = ["KB", "MB", "GB", "TB"]

    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} PB"

def get_parent_path(path: PathString) -> str:
    """Getting the parent directory based on Windows paths"""
    path = os.path.normpath(str(path))
    parent = os.path.dirname(path)

    if not parent:
        return path

    if len(parent) == 2 and parent[1] == ":":
        parent += os.sep

    return parent

def safe_windows_listdir(path: PathString) -> List[str]:
    """
    Secure access to directory contents in Windows
    :return: list of paths or empty list if not accessible"""
    try:
        return os.listdir(path)

    except PermissionError:
        return []

    except FileNotFoundError:
        return []

    except OSError:
        return []

def is_hidden_windows_file(path: PathString) -> bool:
    """
    Checking if a file is hidden in Windows
    :return: True if hidden, False otherwise
    """
    if not is_windows_os():
        return False
    if not os.path.exists(path):
        return False

    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))

        if attributes == -1:
            return False

        return bool(attributes & FILE_ATTRIBUTE_HIDDEN)

    except (OSError, AttributeError):
        return False


def validate_windows_path_recursive(path: PathString, depth: int = 0) -> Tuple[bool, List[str]]:
    """
    Recursive checking of a path and all its parent directories in Windows
    :return: (validity, list of problematic sections of the path)
    """
    path = str(path)
    problematic_sections = []

    if depth > MAX_DEPTH:
        return (False, ["Превышена максимальная глубина рекурсии"])

    is_valid, error_msg = validate_windows_path(path)
    if not is_valid:
        problematic_sections.append(f"{path}: {error_msg}")

    parent = get_parent_path(path)

    if parent == path:
        return (len(problematic_sections) == 0, problematic_sections)

    parent_valid, parent_problems = validate_windows_path_recursive(parent, depth + 1)

    problematic_sections.extend(parent_problems)

    return (len(problematic_sections) == 0, problematic_sections)


def collect_windows_metadata_recursive(path: PathString,
                                       max_depth: int = 10,
                                       current_depth: int = 0) -> Dict[str, Any]:
    """
    Recursive collection of Windows file system metadata
    :return: nested dict with file system metadata
    """
    path = str(path)

    if current_depth >= max_depth:
        return {
            "name": os.path.basename(path),
            "path": path,
            "depth": current_depth,
            "warning": "Достигнута максимальная глубина рекурсии",
            "files": {},
            "directories": []
        }

    if not os.path.exists(path):
        return {
            "name": os.path.basename(path),
            "path": path,
            "depth": current_depth,
            "error": "Пути не существует",
            "files": {},
            "directories": []
        }

    if not os.path.isdir(path):
        return {
            "name": os.path.basename(path),
            "path": path,
            "error": "Путь не является директорией",
            "files": {},
            "directories": []
        }

    items = safe_windows_listdir(path)

    files_stats = {
        "count": 0,
        "total_size": 0,
        "extensions": {},
        "attributes": {
            "hidden": 0,
            "system": 0,
            "readonly": 0
        }
    }

    directories_list = []

    for item_name in items:
        item_path = os.path.join(path, item_name)

        if os.path.isfile(item_path):
            files_stats["count"] += 1

            try:
                size = os.path.getsize(item_path)
                files_stats["total_size"] += size
            except OSError:
                pass

            _, ext = os.path.splitext(item_name)
            ext = ext.lower() if ext else "without extension"
            files_stats["extensions"][ext] = files_stats["extensions"].get(ext, 0) + 1

            try:
                attributes = ctypes.windll.kernel32.GetFileAttributesW(item_path)
                if attributes != -1:
                    if attributes & FILE_ATTRIBUTE_HIDDEN:
                        files_stats["attributes"]["hidden"] += 1
                    if attributes & FILE_ATTRIBUTE_SYSTEM:
                        files_stats["attributes"]["system"] += 1
                    if attributes & FILE_ATTRIBUTE_READONLY:
                        files_stats["attributes"]["readonly"] += 1
            except (OSError, AttributeError):
                pass

        elif os.path.isdir(item_path):
            sub_metadata = collect_windows_metadata_recursive(
                item_path,
                max_depth,
                current_depth + 1
            )
            directories_list.append(sub_metadata)

    result = {
        "name": os.path.basename(path),
        "path": path,
        "depth": current_depth,
        "files": {
            "count": files_stats["count"],
            "total_size": files_stats["total_size"],
            "total_size_formatted": format_size(files_stats["total_size"]),
            "extensions": files_stats["extensions"],
            "attributes": files_stats["attributes"]
        },
        "directories": directories_list
    }

    return result


def resolve_long_paths_recursive(path: PathString,
                                 prefix: str = "\\\\?\\",
                                 depth: int = 0) -> str:
    """
    Recursive conversion of long Windows paths with UNC support
    :return: path with prefix
    """
    path = str(path)

    if depth > MAX_DEPTH:
        return path

    if path.startswith(prefix) or path.startswith("\\\\?\\UNC\\"):
        return path

    if len(path) > 260:
        if path.startswith("\\\\"):
            return prefix + "UNC\\" + path[2:]
        else:
            return prefix + path

    parent = get_parent_path(path)

    if parent and parent != path:
        resolve_long_paths_recursive(parent, prefix, depth + 1)

    return path