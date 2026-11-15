import os
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import utils
import navigation

def count_files(path: str) -> Tuple[bool, int]:
    count = 0

    if not os.path.exists(path):
        return False, 0

    if os.path.isfile(path):
        if utils.is_hidden_windows_file(path):
            return True, 0
        return True, 1

    if os.path.isdir(path):
        safe_items = utils.safe_windows_listdir(path)
        success, items = navigation.list_directory(path)

        if not success:
            return False, 0

        for item in items:
            if item['name'] not in safe_items:
                continue

            full_path = os.path.join(path, item['name'])

            if os.path.islink(full_path):
                continue

            if item['type'] == 'file':
                if item['hidden']:
                    continue
                count += 1

            elif item['type'] == 'directory':
                subsuccess, subcount = count_files(full_path)
                if subsuccess == False:
                    return False, 0
                count += subcount

        return True, count

    return False, 0


def count_bytes(path: str) -> Tuple[bool, int]:
    count = 0

    if not os.path.exists(path):
        return False, 0

    if os.path.isfile(path):
        if utils.is_hidden_windows_file(path):
            return True, 0

        try:
            return True, os.path.getsize(path)
        except (PermissionError, FileNotFoundError, OSError):
            return True, 0

    if os.path.isdir(path):
        safe_items = utils.safe_windows_listdir(path)
        success, items = navigation.list_directory(path)

        if not success:
            return False, 0

        for item in items:
            if item['name'] not in safe_items:
                continue

            full_path = os.path.join(path, item['name'])

            if os.path.islink(full_path):
                continue

            if item['type'] == 'file':
                if item['hidden']:
                    continue
                try:
                    count += os.path.getsize(full_path)
                except (PermissionError, FileNotFoundError, OSError):
                    continue

            elif item['type'] == 'directory':
                subsuccess, subcount = count_bytes(full_path)

                if subsuccess == False:
                    return False, 0

                count += subcount

        return True, count

    return False, 0


def analyze_windows_file_types(path: str) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    info = {}

    if not os.path.exists(path):
        return False, {}

    if os.path.isfile(path):
        if utils.is_hidden_windows_file(path):
            return True, {}

        extension = os.path.splitext(path)[1].lower()

        if not extension:
            extension = 'without extension'

        try:
            size = os.path.getsize(path)
        except (PermissionError, FileNotFoundError, OSError):
            return True, {}

        info[extension] = {
            'count': 1,
            'total_size': size
        }

        return True, info

    if os.path.isdir(path):
        safe_items = utils.safe_windows_listdir(path)
        success, items = navigation.list_directory(path)

        if not success:
            return False, {}

        for item in items:
            if item['name'] not in safe_items:
                continue

            full_path = os.path.join(path, item['name'])

            if os.path.islink(full_path):
                continue

            if item['type'] == 'file':
                if item['hidden']:
                    continue

                extension = os.path.splitext(item['name'])[1].lower()

                if not extension:
                    extension = 'without extension'

                if extension not in info:
                    info[extension] = {'count': 0, 'total_size': 0}

                try:
                    size = os.path.getsize(full_path)
                except (PermissionError, FileNotFoundError, OSError):
                    continue

                info[extension]['total_size'] += size
                info[extension]['count'] += 1

            elif item['type'] == 'directory':
                subsuccess, subinfo = analyze_windows_file_types(full_path)

                if subsuccess == False:
                    return False, {}

                for extension, stats in subinfo.items():
                    if extension not in info:
                        info[extension] = {'count': 0, 'total_size': 0}

                    info[extension]['count'] += stats['count']
                    info[extension]['total_size'] += stats['total_size']

        return True, info

    return False, {}


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    stats = {'hidden': 0, 'system': 0, 'readonly': 0}

    if not os.path.exists(path):
        return stats

    if os.path.isfile(path):
        if os.path.islink(path):
            return stats

        if utils.is_hidden_windows_file(path):
            stats['hidden'] += 1

        try:
            attributes = os.stat(path).st_file_attributes

            if attributes & utils.FILE_ATTRIBUTE_SYSTEM:
                stats['system'] += 1

            if attributes & utils.FILE_ATTRIBUTE_READONLY:
                stats['readonly'] += 1

        except (PermissionError, FileNotFoundError, OSError):
            pass

        return stats

    if os.path.isdir(path):
        safe_items = utils.safe_windows_listdir(path)
        success, items = navigation.list_directory(path)

        if not success:
            return stats

        for item in items:
            if item['name'] not in safe_items:
                continue

            full_path = os.path.join(path, item['name'])

            if os.path.islink(full_path):
                continue

            if item['type'] == 'file':
                if utils.is_hidden_windows_file(full_path):
                    stats['hidden'] += 1

                try:
                    attributes = os.stat(full_path).st_file_attributes

                    if attributes & utils.FILE_ATTRIBUTE_SYSTEM:
                        stats['system'] += 1

                    if attributes & utils.FILE_ATTRIBUTE_READONLY:
                        stats['readonly'] += 1

                except (PermissionError, FileNotFoundError, OSError, AttributeError):
                    continue

            elif item['type'] == 'directory':
                substats = get_windows_file_attributes_stats(full_path)

                stats['hidden'] += substats['hidden']
                stats['system'] += substats['system']
                stats['readonly'] += substats['readonly']

        return stats

    return stats


def show_windows_directory_stats(path: str) -> bool:
    if not os.path.exists(path):
        print('Указанный путь не существует')
        return False

    if not os.path.isfile(path) and not os.path.isdir(path):
        print('Указанный путь не является файлом или каталогом')
        return False

    success, files_count = count_files(path)

    if not success:
        print('Не удалось посчитать файлы')
        return False

    success, total_bytes = count_bytes(path)

    if not success:
        print('Не удалось подсчитать размер файлов')
        return False

    success, file_types = analyze_windows_file_types(path)

    if not success:
        print('Не удалось проанализировать типы файлов')
        return False

    attributes_stats = get_windows_file_attributes_stats(path)

    largest_files = []
    directories_count = 0
    directories_to_check = []

    if os.path.isdir(path):
        directories_to_check.append(path)

    elif os.path.isfile(path) and not os.path.islink(path):
        if not utils.is_hidden_windows_file(path):
            try:
                size = os.path.getsize(path)
                largest_files.append((size, path))
            except (PermissionError, FileNotFoundError, OSError):
                pass

    while directories_to_check:
        current_path = directories_to_check.pop()

        success, items = navigation.list_directory(current_path)

        if not success:
            continue

        for item in items:
            full_path = os.path.join(current_path, item['name'])

            if os.path.islink(full_path):
                continue

            if item['type'] == 'file':
                if item['hidden']:
                    continue

                try:
                    size = os.path.getsize(full_path)
                    largest_files.append((size, full_path))
                except (PermissionError, FileNotFoundError, OSError):
                    continue

            elif item['type'] == 'directory':
                directories_count += 1
                directories_to_check.append(full_path)

    largest_files.sort(reverse=True)
    print('========== СТАТИСТИКА КАТАЛОГА ==========')

    print(f'Путь: {path}')

    print('===== Общая информация =====')
    print(f'Количество файлов: {files_count}')
    print(f'Количество папок: {directories_count}')
    print(f'Общий размер: {utils.format_size(total_bytes)}')

    print('--- Распределение по типам файлов ---')

    if file_types:
        for extension, stats in sorted(file_types.items()):
            print(
                f'{extension}: '
                f"{stats['count']} файлов, "
                f"{utils.format_size(stats['total_size'])}"
            )
    else:
        print('Файлы не найдены')

    print('--- Атрибуты файлов ---')
    print(f'Скрытые: {attributes_stats["hidden"]}')
    print(f'Системные: {attributes_stats["system"]}')
    print(f'Только для чтения: {attributes_stats["readonly"]}')

    print('--- 5 крупнейших файлов ---')

    if largest_files:
        for size, file_path in largest_files[:5]:
            print(f'{file_path} — {utils.format_size(size)}')
    else:
        print('Файлы не найдены')

    return True
