import minecraft_launcher_lib
import subprocess
import os
import uuid
import platform
import requests
import shutil
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class Launcher(QObject):
    # Сигнал для отправки сообщений в GUI
    status_update = pyqtSignal(str)
    # Сигнал о завершении работы
    finished = pyqtSignal()

def download_tlauncher_libs(minecraft_dir):
    """
    Скачивает и размещает кастомные библиотеки TLauncher для обхода проверки авторизации.
    """
    print("Проверяем/скачиваем кастомные библиотеки TLauncher...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    libs_to_download = {
        "authlib": {
            "url": "http://res.tlauncher.org/unb/libraries/org/tlauncher/authlib/2.0.28.12/authlib-2.0.28.12.jar",
            "path": os.path.join(minecraft_dir, "libraries", "org", "tlauncher", "authlib", "2.0.28.12", "authlib-2.0.28.12.jar")
        },
        "patchy": {
            "url": "https://res.tlauncher.org/unb/libraries/org/tlauncher/patchy/1.3.9/patchy-1.3.9.jar",
            "path": os.path.join(minecraft_dir, "libraries", "org", "tlauncher", "patchy", "1.3.9", "patchy-1.3.9.jar")
        }
    }

    for lib_name, lib_info in libs_to_download.items():
        lib_path = lib_info["path"]
        if not os.path.exists(lib_path):
            print(f"Скачиваем {lib_name}...")
            try:
                os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                response = requests.get(lib_info["url"], headers=headers)
                response.raise_for_status()  # Проверка на ошибки HTTP
                with open(lib_path, 'wb') as f:
                    f.write(response.content)
                print(f"{lib_name} успешно скачан.")
            except requests.RequestException as e:
                print(f"Ошибка при скачивании {lib_name}: {e}")
                return None, None

    return libs_to_download["authlib"]["path"], libs_to_download["patchy"]["path"]

class GameLauncher(QObject):
    # Сигналы для обновления GUI
    status_update = pyqtSignal(str)
    launch_finished = pyqtSignal()

    def __init__(self, nickname, profile_name, profile_data, minecraft_directory):
        super().__init__()
        self.nickname = nickname
        self.profile_name = profile_name
        self.profile_data = profile_data
        self.minecraft_directory = minecraft_directory
        self.version = profile_data['minecraft_version']
        self.mod_loader = profile_data['mod_loader']
        self.ram_mb = profile_data.get('ram_mb', 2048) # Память в МБ, по умолчанию 2ГБ

    def run(self):
        """Запускает весь процесс в отдельном потоке"""
        try:
            self.launch_game()
        except Exception as e:
            self.status_update.emit(f"Критическая ошибка: {e}")
        finally:
            self.launch_finished.emit()

    def _is_version_legacy(self):
        """Проверяет, является ли версия "старой" (до 1.17)."""
        try:
            # Сравниваем только мажорную и минорную части версии
            version_tuple = tuple(map(int, self.version.split('.')[:2]))
            return version_tuple <= (1, 16)
        except ValueError:
            # Если не удалось распарсить, считаем версию новой на всякий случай
            return False

    def launch_game(self):
        # Игровая директория теперь - это папка профиля внутри папки versions
        game_directory = os.path.join(self.minecraft_directory, "versions", self.profile_name)
        # Убедимся, что все нужные папки существуют
        os.makedirs(os.path.join(game_directory, "mods"), exist_ok=True)
        os.makedirs(os.path.join(game_directory, "resourcepacks"), exist_ok=True)
        os.makedirs(os.path.join(game_directory, "shaderpacks"), exist_ok=True)


        self.status_update.emit(f"Добро пожаловать в Dark.Base.Minecraft.Launcher!")
        self.status_update.emit(f"Запуск профиля: {self.profile_name}")

        # Callback-функции для minecraft-launcher-lib
        callback = {
            "setStatus": lambda text: self.status_update.emit(text),
            "setProgress": lambda value: None, # Мы не будем использовать прогресс-бар в этом примере
            "setMax": lambda value: None
        }

        # Используем хак с TLauncher только для старых версий
        use_tlauncher_hack = self._is_version_legacy()
        if use_tlauncher_hack:
            authlib_path, patchy_path = download_tlauncher_libs(self.minecraft_directory)
            if not authlib_path or not patchy_path:
                self.status_update.emit("Не удалось скачать необходимые библиотеки. Запуск невозможен.")
                return

        self.status_update.emit(f"Проверяем наличие версии {self.version}...")
        minecraft_launcher_lib.install.install_minecraft_version(
            version=self.version,
            minecraft_directory=self.minecraft_directory,
            callback=callback
        )
        self.status_update.emit(f"Версия {self.version} успешно установлена/проверена.")

        version_to_launch = self.version
        if self.mod_loader != "vanilla":
            try:
                self.status_update.emit(f"Проверяем/устанавливаем {self.mod_loader.capitalize()}...")
                loader = minecraft_launcher_lib.mod_loader.get_mod_loader(self.mod_loader)
                latest_loader_version = loader.get_latest_loader_version(self.version)
                self.status_update.emit(f"Найдена последняя версия {self.mod_loader.capitalize()}: {latest_loader_version}")
                
                # Очищаем папку natives перед установкой, чтобы избежать ошибки [WinError 183]
                version_id = f"{self.version}-{self.mod_loader}-{latest_loader_version}"
                natives_dir = os.path.join(self.minecraft_directory, "versions", version_id, "natives")
                if os.path.isdir(natives_dir):
                    shutil.rmtree(natives_dir)

                loader.install(self.version, self.minecraft_directory, loader_version=latest_loader_version, callback=callback)
                
                if self.mod_loader == "forge":
                    version_to_launch = f"{self.version}-forge-{latest_loader_version}"
                elif self.mod_loader == "fabric":
                    version_to_launch = f"fabric-loader-{latest_loader_version}-{self.version}"
                elif self.mod_loader == "neoforge":
                    version_to_launch = f"{self.version}-neoforge-{latest_loader_version}"
                
                self.status_update.emit(f"{self.mod_loader.capitalize()} успешно установлен. Версия для запуска: {version_to_launch}")
            except Exception as e:
                self.status_update.emit(f"Не удалось установить {self.mod_loader.capitalize()}: {e}. Запускаем ванильную версию.")
                version_to_launch = self.version

        # Для новых версий используем UUID в качестве токена, чтобы разблокировать мультиплеер
        token = "0" if use_tlauncher_hack else str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{self.nickname}"))

        options = {
            "username": self.nickname,
            "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{self.nickname}")),
            "token": token,
            "gameDirectory": game_directory, # Указываем изолированную папку профиля
            "jvmArguments": [ # Устанавливаем выделенную память
                f"-Xmx{self.ram_mb}M",
                f"-Xms{self.ram_mb}M"
            ]
        }

        # ВАЖНО: хук для плагинов теперь вызывается в gui.py перед созданием GameLauncher,
        # поэтому здесь мы просто используем уже обработанные profile_data.
        # options["jvmArguments"] уже содержит правильное значение RAM из profile_data.

        self.status_update.emit(f"Генерируем команду для запуска от имени '{self.nickname}'...")
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
            version=version_to_launch,
            minecraft_directory=self.minecraft_directory, # Основная директория для версий и библиотек
            options=options
        )

        if use_tlauncher_hack:
            try:
                cp_index = minecraft_command.index("-cp")
            except ValueError:
                cp_index = minecraft_command.index("-classpath")

            separator = ";" if platform.system() == "Windows" else ":"
            tlauncher_libs = f"{authlib_path}{separator}{patchy_path}"
            minecraft_command[cp_index + 1] = tlauncher_libs + separator + minecraft_command[cp_index + 1]
            self.status_update.emit("Кастомные библиотеки успешно добавлены в команду запуска.")

        self.status_update.emit("Запускаем Minecraft...")
        try:
            process = subprocess.Popen(minecraft_command)
            process.wait()
            self.status_update.emit("Процесс Minecraft завершен.")
        except Exception as e:
            self.status_update.emit(f"Произошла ошибка при запуске: {e}")
