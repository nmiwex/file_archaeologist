import os
import sys
import platform
from typing import NoReturn
import utils
import navigation
import analysis
import search
from datetime import datetime

def check_windows_environment() -> bool:
    """Checking that the program is running on Windows"""
    if not utils.is_windows_os():
        print("Ошибка: программа работает только в Windows!")
        sys.exit(1)
    return utils.is_windows_os()


def display_windows_banner() -> None:
    """Displaying a banner with information about Windows"""
    current_drive = navigation.get_current_drive()
    os_version = platform.version()
    architecture = platform.machine()
    computer_name = platform.node()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 50)
    print("         WINDOWS FILE MANAGER v1.0  ")
    print("=" * 50)
    print(f"  Компьютер:            {computer_name}")
    print(f"  Операционная система: Windows {os_version}")
    print(f"  Текущий диск:         {current_drive}")
    print(f"  Архитектура:          {architecture}")
    print(f"  Дата и время:         {current_time}")
    print("=" * 50)
    print()


def display_main_menu(current_path: str) -> None:
    """Displaying the main menu for Windows"""
    drives = navigation.list_available_drives()

    print(f"\n Текущий путь: {current_path}")
    print(f" Доступные диски: {', '.join(drives)}")
    print()

    print("=" * 50)
    print("           ГЛАВНОЕ МЕНЮ")
    print("=" * 50)
    print("  1.  Навигация по файловой системе")
    print("  2.  Анализ директории")
    print("  3.  Поиск файлов")
    print("  4.  Статистика файловой системы")
    print("  5.  Сменить диск")
    print("  6.  Список содержимого папки")
    print("  0.  Выход из программы")
    print("=" * 50)
    print()


def handle_windows_navigation(command: str, current_path: str) -> str:
    """Handling navigation commands in Windows"""
    if command == "1":
        success, items = navigation.list_directory(current_path)
        if success:
            navigation.format_directory_output(items)
        else:
            print(" Не удалось получить содержимое папки")

        action = input("\n Введите имя папки для перехода (или '..' для возврата): ").strip()

        if action == "..":
            new_path = navigation.move_up(current_path)
            if new_path != current_path:
                print(f" Переход в: {new_path}")
                return new_path
            else:
                print(" Вы уже в корневом каталоге")
                return current_path
        else:
            success, new_path = navigation.move_down(current_path, action)
            if success:
                print(f" Переход в: {new_path}")
                return new_path
            else:
                print(f" Папка '{action}' не найдена или недоступна")
                return current_path

    elif command == "5":
        drives = navigation.list_available_drives()
        print("\nДоступные диски:")
        for i, drive in enumerate(drives, 1):
            print(f"  {i}. {drive}")

        choice = input("\nВыберите номер диска: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(drives):
                new_drive = drives[idx]
                print(f"Смена диска на: {new_drive}")
                return new_drive
            else:
                print("Неверный номер диска")
        except ValueError:
            print("Ошибка ввода")
        return current_path

    elif command == "6":
        success, items = navigation.list_directory(current_path)
        if success:
            navigation.format_directory_output(items)
        else:
            print("Не удалось получить содержимое папки")
        return current_path

    else:
        print(f"Неизвестная команда навигации: {command}")
        return current_path

def handle_windows_analysis(command: str, current_path: str) -> None:
    """Обработка команд анализа Windows файловой системы"""
    # TODO: Использовать analysis.show_windows_directory_stats()
    # и другие функции анализа
    pass

def handle_windows_search(command: str, current_path: str) -> None:
    """Обработка команд поиска в Windows"""
    # TODO: Использовать search.search_menu_handler()
    pass

def run_windows_command(command: str, current_path: str) -> str:
    """Главный обработчик команд с использованием match case"""
    # TODO: Использовать match case для маршрутизации команд
    # Интегрировать ВСЕ модули:
    # - navigation для команд 1, 5, 6
    # - analysis для команд 2, 4
    # - search для команды 3
    # Вернуть обновленный текущий путь
    match command:
        case "1" | "5" | "6":
            return handle_windows_navigation(command, current_path)
        case "2" | "4":
            return handle_windows_analysis(command, current_path)
        case "3":
            return handle_windows_search(command, current_path)
        case "0":
            print("\nДо свидания! Программа завершена.")
            sys.exit(0)
        case _:
            print(f"Неизвестная команда: '{command}'")
            print("Пожалуйста, выберите команду из меню (0-6)")
            return current_path

def main() -> NoReturn:
    """The main function of the program for Windows"""
    if not check_windows_environment():
        sys.exit(1)

    display_windows_banner()

    current_path = os.getcwd()

    while True:
        try:
            display_main_menu(current_path)
            command = input(" Введите номер команды: ").strip()

            if not command:
                continue

            current_path = run_windows_command(command, current_path)

        except KeyboardInterrupt:
            print("\n\nПрервано пользователем (Ctrl+C)")
            print("До свидания!")
            sys.exit(0)

        except Exception as e:
            print(f"\n Произошла ошибка: {e}")
            print("   Попробуйте ещё раз.")


if __name__ == "__main__":
    main()