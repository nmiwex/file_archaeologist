import os
import re
import fnmatch
from typing import List, Dict, Any, Tuple
import utils  # Функции архитектора
import navigation  # Функции инженера навигации
import analysis  # Функции аналитика


def find_files_windows(pattern: str, path: str, case_sensitive: bool = False) -> List[str]:
    """Поиск файлов по шаблону в Windows"""

    found_files = []

    is_valid, _ = utils.validate_windows_path(path)
    if not is_valid:
        return found_files

    success, total_files = analysis.count_files(path)
    if success:
        print(f"[*] Начинаем поиск. Всего файлов в директории (без скрытых): {total_files}")

    escaped_pattern = re.escape(pattern)
    regex_pattern = escaped_pattern.replace(r'\*', '.*').replace(r'\?', '.')
    if not case_sensitive:
        regex_pattern = regex_pattern.lower()

    try:
        success_dir, items = navigation.list_directory(path)
        if not success_dir or not items:
            return found_files

        for item in items:
            name = item.get('name', '')
            item_type = item.get('type', 'Unknown')
            item_path = os.path.join(path, name)

            if item_type == 'directory':
                found_files.extend(find_files_windows(pattern, item_path, case_sensitive))
            elif item_type == 'file':
                match_name = name if case_sensitive else name.lower()

                if re.fullmatch(regex_pattern, match_name):
                    found_files.append(item_path)
    except Exception:
        pass

    return found_files


def find_by_windows_extension(extensions: List[str], path: str) -> List[str]:
    """Поиск файлов по списку расширений Windows"""

    found_files = []
    exts_lower = [ext.lower() if ext.startswith('.') else f".{ext.lower()}" for ext in extensions]

    try:
        success, items = navigation.list_directory(path)
        if not success or not items:
            return found_files

        for item in items:
            name = item.get('name', '')
            item_type = item.get('type', 'Unknown')
            item_path = os.path.join(path, name)

            if item_type == 'directory':
                found_files.extend(find_by_windows_extension(extensions, item_path))
            elif item_type == 'file':
                _, ext = os.path.splitext(name)
                if ext.lower() in exts_lower:
                    found_files.append(item_path)
    except Exception:
        pass

    return found_files


def find_large_files_windows(min_size_mb: float, path: str) -> List[Dict[str, Any]]:
    """Поиск крупных файлов в Windows"""

    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024

    try:
        success, items = navigation.list_directory(path)
        if not success or not items:
            return large_files

        for item in items:
            name = item.get('name', '')
            item_type = item.get('type', 'Unknown')
            item_path = os.path.join(path, name)

            if item_type == 'directory':
                large_files.extend(find_large_files_windows(min_size_mb, item_path))
            elif item_type == 'file':
                success_bytes, size = analysis.count_bytes(item_path)
                if not success_bytes:
                    size = item.get('size', 0)  # Фолбэк на размер из Навигатора

                if size >= min_size_bytes:
                    _, ext = os.path.splitext(name)
                    large_files.append({
                        'path': item_path,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'type': ext.lower()
                    })
    except Exception:
        pass

    return large_files


def find_windows_system_files(path: str) -> List[str]:
    """Поиск системных файлов Windows"""

    system_files = []
    special_folders = navigation.get_windows_special_folders()

    windows_root = os.environ.get('SystemRoot', 'C:\\Windows')
    search_roots = [windows_root]

    if special_folders:
        search_roots.extend(special_folders.values())

    target_files = [
        'ntoskrnl.exe', 'hal.dll', 'win.ini', 'system.ini',
        'boot.ini', 'ntldr', 'bootmgr', 'pagefile.sys', 'hiberfil.sys'
    ]

    def _recursive_search(current_path):
        try:
            success, items = navigation.list_directory(current_path)
            if not success or not items:
                return

            for item in items:
                name = item.get('name', '')
                item_type = item.get('type', 'Unknown')
                item_path = os.path.join(current_path, name)

                if item_type == 'directory':
                    _recursive_search(item_path)
                elif item_type == 'file':
                    if name.lower() in target_files or (
                            name.lower().endswith('.sys') and 'windows' in current_path.lower()):
                        system_files.append(item_path)
        except Exception:
            pass

    for root in search_roots:
        _recursive_search(root)

    return system_files


def search_menu_handler(current_path: str) -> bool:
    """Обработчик меню поиска для Windows"""

    print("\n--- Меню поиска цифровых артефактов ---")
    print("1. Поиск по шаблону имени (например, *.txt)")
    print("2. Поиск по расширениям (например, .exe, .dll)")
    print("3. Поиск больших файлов (в МБ)")
    print("4. Поиск системных файлов Windows")
    print("0. Вернуться в главное меню")

    choice = input("Выберите действие: ").strip()

    match choice:
        case '1':
            pattern = input("Введите шаблон (например, *.txt): ").strip()
            if not pattern:
                pattern = "*"
            print(f"Идет поиск по шаблону '{pattern}' в {current_path}...")
            results = find_files_windows(pattern, current_path)
            format_windows_search_results(results, "Поиск по шаблону")

        case '2':
            exts_input = input("Введите расширения через запятую (например, .exe, .dll): ").strip()
            if exts_input:
                exts = [e.strip() for e in exts_input.split(',')]
                print(f"Идет поиск по расширениям {exts}...")
                results = find_by_windows_extension(exts, current_path)
                format_windows_search_results(results, "Поиск по расширениям")

        case '3':
            try:
                min_size = float(input("Введите минимальный размер в МБ: ").strip())
                print(f"Идет поиск файлов больше {min_size} МБ...")
                results = find_large_files_windows(min_size, current_path)
                format_windows_search_results(results, "Поиск больших файлов")
            except ValueError:
                print("Ошибка: введите корректное число.")

        case '4':
            print("Идет поиск системных файлов Windows...")
            results = find_windows_system_files(current_path)
            format_windows_search_results(results, "Поиск системных файлов")

        case '0':
            return False

        case _:  # Аналог default в switch-case
            print("Неверный выбор. Попробуйте снова.")

    return True


def format_windows_search_results(results: List, search_type: str) -> None:
    """Форматированный вывод результатов поиска для Windows"""

    if not results:
        print(f"\n[{search_type}] Ничего не найдено.")
        return

    print(f"\n[{search_type}] Найдено объектов: {len(results)}")
    print("-" * 75)
    print(f"{'Размер':>12} | {'Тип':<10} | {'Путь'}")
    print("-" * 75)

    for item in results:
        if isinstance(item, dict):
            path_str = item.get('path', '')
            size_mb = item.get('size_mb', 0)
            ext = item.get('type', '')
            size_formatted = utils.format_size(int(size_mb * 1024 * 1024))
            print(f"{size_formatted:>12} | {ext:<10} | {path_str}")
        else:
            path_str = str(item)
            size_formatted = "N/A"
            _, ext = os.path.splitext(path_str)

            attrs = analysis.get_windows_file_attributes_stats(path_str)
            attr_str = []
            if attrs.get('hidden'): attr_str.append('H')
            if attrs.get('system'): attr_str.append('S')
            if attrs.get('readonly'): attr_str.append('R')
            attr_flags = f"[{''.join(attr_str)}]" if attr_str else ""

            try:
                if os.path.exists(path_str):
                    size_bytes = os.path.getsize(path_str)
                    size_formatted = utils.format_size(size_bytes)
            except Exception:
                pass

            print(f"{size_formatted:>12} | {ext:<10} | {path_str} {attr_flags}")

    print("-" * 75)
