import shutil
import sys
import os
import json
import threading
from PyQt6.QtWidgets import (QApplication, QCheckBox, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QComboBox,
                             QTextEdit, QLabel, QListWidget, QListWidgetItem,
                             QFileDialog, QDialog, QFormLayout, QSpinBox, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt
import minecraft_launcher_lib

# Импортируем менеджер плагинов
from plugin_manager import PluginManager

# Импортируем наш класс для запуска игры
from main import GameLauncher

# Путь к директории Minecraft
MINECRAFT_DIRECTORY = os.path.join(os.getenv("APPDATA"), ".minecraft_dark_base")
# Файл для хранения информации о профилях
PROFILES_FILE = os.path.join(MINECRAFT_DIRECTORY, "profiles.json")
# Файл для хранения настроек
SETTINGS_FILE = os.path.join(MINECRAFT_DIRECTORY, "settings.json")

# Стили QSS, адаптированные из вашего CSS-файла
HACKER_STYLE = """
    QWidget {
        background-color: #050a05;
        color: #00ff41;
        font-family: 'Fira Code', monospace;
        font-size: 14px;
        text-shadow: 0 0 2px #00ff41;
    }
    QMainWindow {
        border: 1px solid #00520e;
    }
    QLabel {
        text-shadow: none;
    }
    QLineEdit, QComboBox, QTextEdit {
        background-color: rgba(0, 20, 0, 0.3);
        border: 1px solid #00520e;
        padding: 5px;
    }
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 1px solid #00ff41;
        background-color: rgba(0, 255, 65, 0.05);
    }
    QPushButton {
        background-color: #008f11;
        color: #050a05;
        border: 1px solid #00ff41;
        padding: 8px 12px;
        text-shadow: none;
    }
    QPushButton:hover {
        background-color: #00ff41;
        box-shadow: 0 0 10px #00ff41;
    }
    QPushButton:disabled {
        background-color: #222;
        color: #00520e;
        border-color: #00520e;
    }
    QListWidget {
        background-color: rgba(0, 20, 0, 0.3);
        border: 1px solid #00520e;
    }
    QListWidget::item:hover {
        background-color: rgba(0, 255, 65, 0.1);
    }
"""

class ProfileDialog(QDialog):
    """Диалоговое окно для создания/редактирования профиля."""
    def __init__(self, parent=None, profile_name="", profile_data=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки профиля")

        if profile_data is None:
            profile_data = {}

        layout = QFormLayout(self)

        self.name_input = QLineEdit(profile_name)
        self.name_input.setPlaceholderText("Название сборки")
        layout.addRow("Название профиля:", self.name_input)

        self.version_combo = QComboBox()
        
        if settings is None:
            settings = {}

        # Получаем полный список версий от Mojang
        try:
            all_versions = minecraft_launcher_lib.utils.get_version_list()
            
            versions_to_show = []
            for v in all_versions:
                if v['type'] == 'release':
                    versions_to_show.append(v['id'])
                elif v['type'] == 'snapshot' and settings.get('show_snapshots', False):
                    versions_to_show.append(v['id'])
                elif v['type'] in ('old_alpha', 'old_beta') and settings.get('show_historical', False):
                    versions_to_show.append(v['id'])

            # Сортируем версии, чтобы новые были вверху (необязательно, но удобно)
            # Это простая сортировка, которая может быть не идеальна для всех форматов версий
            versions_to_show.sort(key=lambda s: list(map(int, s.split('.')[:2])) if s.replace('.', '').isdigit() else [0], reverse=True)
            
            self.version_combo.addItems(versions_to_show)

        except Exception as e:
            print(f"Не удалось получить список версий: {e}. Используется базовый список.")
            self.version_combo.addItems(["1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2"])

        if "minecraft_version" in profile_data:
            self.version_combo.setCurrentText(profile_data["minecraft_version"])
        layout.addRow("Версия Minecraft:", self.version_combo)

        self.modloader_combo = QComboBox()
        self.modloader_combo.addItems(["vanilla", "forge", "fabric", "neoforge"])
        if "mod_loader" in profile_data:
            self.modloader_combo.setCurrentText(profile_data["mod_loader"])
        layout.addRow("Модлоадер:", self.modloader_combo)

        self.ram_spinbox = QSpinBox()
        self.ram_spinbox.setRange(1024, 16384)
        self.ram_spinbox.setSingleStep(512)
        self.ram_spinbox.setSuffix(" МБ")
        self.ram_spinbox.setValue(profile_data.get("ram_mb", 2048))
        layout.addRow("Оперативная память (RAM):", self.ram_spinbox)

        buttons = QHBoxLayout()
        ok_button = QPushButton("Сохранить")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def get_data(self):
        """Возвращает данные из диалога."""
        # Этот метод не используется напрямую, но может быть полезен для расширения
        return self.name_input.text(), self.version_combo.currentText(), self.modloader_combo.currentText(), self.ram_spinbox.value()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dark.Base.Minecraft.Launcher")
        self.setGeometry(100, 100, 600, 550)

        # Загружаем настройки
        self.settings = self.load_settings()

        # Создаем систему вкладок
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- ВКЛАДКА "ЗАПУСК" ---
        self.launch_tab = QWidget()
        self.tabs.addTab(self.launch_tab, "Запуск")
        main_layout = QVBoxLayout(self.launch_tab)

        # --- Верхняя часть ---
        top_layout = QHBoxLayout()

        # Левая колонка (настройки)
        launch_settings_layout = QVBoxLayout()

        # Никнейм вынесен наверх, так как он общий
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Введите ник")
        self.nickname_input.setText("Player")
        main_layout.addWidget(QLabel("Никнейм:"))
        main_layout.addWidget(self.nickname_input)

        # Управление профилями
        profile_management_layout = QVBoxLayout()
        profile_management_layout.addWidget(QLabel("Профиль (сборка):"))
        launch_settings_layout.setObjectName("launch_settings_layout") # Даем имя layout для поиска плагинами
        self.profiles_combo = QComboBox()
        self.profiles_combo.currentTextChanged.connect(self.on_profile_selected)
        profile_management_layout.addWidget(self.profiles_combo)

        profile_buttons_layout = QHBoxLayout()
        new_profile_button = QPushButton("Создать")
        new_profile_button.setObjectName("new_profile_button")
        new_profile_button.clicked.connect(self.create_new_profile)
        delete_profile_button = QPushButton("Удалить")
        delete_profile_button.setObjectName("delete_profile_button")
        delete_profile_button.clicked.connect(self.delete_profile)
        import_profile_button = QPushButton("Импорт")
        import_profile_button.setObjectName("import_profile_button")
        import_profile_button.clicked.connect(self.import_profiles)
        analyze_profile_button = QPushButton("Анализ")
        analyze_profile_button.setObjectName("analyze_profile_button")
        analyze_profile_button.clicked.connect(self.analyze_current_profile)
        profile_buttons_layout.addWidget(new_profile_button)
        profile_buttons_layout.addWidget(import_profile_button)
        profile_buttons_layout.addWidget(delete_profile_button)
        profile_buttons_layout.addWidget(analyze_profile_button)
        profile_management_layout.addLayout(profile_buttons_layout)
        launch_settings_layout.addLayout(profile_management_layout)

        # --- Правая колонка (управление файлами профиля) ---
        profile_files_layout = QVBoxLayout()
        self.profile_files_tabs = QTabWidget()
        profile_files_layout.addWidget(self.profile_files_tabs)

        # -- ВКЛАДКА "МОДЫ" --
        mods_tab = QWidget()
        self.profile_files_tabs.addTab(mods_tab, "Моды")
        mods_tab_layout = QVBoxLayout(mods_tab)
        self.mods_list_widget = QListWidget()
        mods_tab_layout.addWidget(self.mods_list_widget)
        mod_buttons_layout = QHBoxLayout()
        add_mod_button = QPushButton("Добавить")
        add_mod_button.setObjectName("add_mod_button")
        add_mod_button.clicked.connect(self.add_mod)
        remove_mod_button = QPushButton("Удалить")
        remove_mod_button.setObjectName("remove_mod_button")
        remove_mod_button.clicked.connect(self.remove_mod)
        mod_buttons_layout.addWidget(add_mod_button)
        mod_buttons_layout.addWidget(remove_mod_button)
        mods_tab_layout.addLayout(mod_buttons_layout)

        # -- ВКЛАДКА "ТЕКСТУРЫ" --
        resourcepacks_tab = QWidget()
        self.profile_files_tabs.addTab(resourcepacks_tab, "Текстуры")
        resourcepacks_tab_layout = QVBoxLayout(resourcepacks_tab)
        self.resourcepacks_list_widget = QListWidget()
        resourcepacks_tab_layout.addWidget(self.resourcepacks_list_widget)
        resourcepack_buttons_layout = QHBoxLayout()
        add_resourcepack_button = QPushButton("Добавить")
        add_resourcepack_button.setObjectName("add_resourcepack_button")
        add_resourcepack_button.clicked.connect(self.add_resourcepack)
        remove_resourcepack_button = QPushButton("Удалить")
        remove_resourcepack_button.setObjectName("remove_resourcepack_button")
        remove_resourcepack_button.clicked.connect(self.remove_resourcepack)
        resourcepack_buttons_layout.addWidget(add_resourcepack_button)
        resourcepack_buttons_layout.addWidget(remove_resourcepack_button)
        resourcepacks_tab_layout.addLayout(resourcepack_buttons_layout)

        # -- ВКЛАДКА "ШЕЙДЕРЫ" --
        shaderpacks_tab = QWidget()
        self.profile_files_tabs.addTab(shaderpacks_tab, "Шейдеры")
        shaderpacks_tab_layout = QVBoxLayout(shaderpacks_tab)
        self.shaderpacks_list_widget = QListWidget()
        shaderpacks_tab_layout.addWidget(self.shaderpacks_list_widget)
        shaderpack_buttons_layout = QHBoxLayout()
        add_shaderpack_button = QPushButton("Добавить")
        add_shaderpack_button.setObjectName("add_shaderpack_button")
        add_shaderpack_button.clicked.connect(self.add_shaderpack)
        remove_shaderpack_button = QPushButton("Удалить")
        remove_shaderpack_button.setObjectName("remove_shaderpack_button")
        remove_shaderpack_button.clicked.connect(self.remove_shaderpack)
        shaderpack_buttons_layout.addWidget(add_shaderpack_button)
        shaderpack_buttons_layout.addWidget(remove_shaderpack_button)
        shaderpacks_tab_layout.addLayout(shaderpack_buttons_layout)

        top_layout.addLayout(launch_settings_layout, 1) # 1 - доля ширины
        top_layout.addLayout(profile_files_layout, 1) # 1 - доля ширины

        main_layout.addLayout(top_layout)

        # --- Средняя часть ---
        self.play_button = QPushButton("Играть")
        self.play_button.setObjectName("play_button") # Даем имя кнопке для кастомизации стилей
        self.play_button.clicked.connect(self.start_game)
        main_layout.addWidget(self.play_button)

        # --- Нижняя часть ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(QLabel("Лог запуска:"))
        main_layout.addWidget(self.log_output)

        # Сохраняем оригинальные действия кнопок для API плагинов
        self.original_actions = {
            "play_button": self.start_game,
            "analyze_profile_button": self.analyze_current_profile
        }

        # Загружаем список профилей при запуске
        self.populate_profiles_list()

        # --- Инициализация и применение плагинов (ПОСЛЕ создания всего UI) ---
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.initialize_plugins()

        # --- ВКЛАДКА "НАСТРОЙКИ" ---
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Настройки")
        settings_layout = QVBoxLayout(self.settings_tab)

        version_settings_layout = QFormLayout()
        
        self.show_snapshots_checkbox = QCheckBox()
        self.show_snapshots_checkbox.setChecked(self.settings.get('show_snapshots', False))
        self.show_snapshots_checkbox.stateChanged.connect(lambda: self.save_setting('show_snapshots', self.show_snapshots_checkbox.isChecked()))
        version_settings_layout.addRow("Показывать снэпшоты:", self.show_snapshots_checkbox)

        self.show_historical_checkbox = QCheckBox()
        self.show_historical_checkbox.setChecked(self.settings.get('show_historical', False))
        self.show_historical_checkbox.stateChanged.connect(lambda: self.save_setting('show_historical', self.show_historical_checkbox.isChecked()))
        version_settings_layout.addRow("Показывать старые (alpha/beta) версии:", self.show_historical_checkbox)

        settings_layout.addLayout(version_settings_layout)
        settings_layout.addStretch() # Добавляет пустое пространство, чтобы прижать настройки к верху

    def save_setting(self, key, value):
        """Сохраняет одну настройку и обновляет файл."""
        self.settings[key] = value
        self.save_settings_data()

    def start_game(self):
        nickname = self.nickname_input.text()
        profile_name = self.profiles_combo.currentText()

        if not nickname:
            self.log_output.append("Ошибка: введите никнейм!")
            return
        if not profile_name:
            self.log_output.append("Ошибка: создайте или выберите профиль!")
            return

        profiles = self.load_profiles_data()
        profile_data = profiles.get(profile_name)

        # Передаем опции запуска через хуки плагинов
        profile_data = self.plugin_manager.run_pre_launch_hooks(profile_data)

        self.play_button.setEnabled(False)
        self.log_output.clear()
        self.log_output.append("Подготовка к запуску...")

        # Создаем экземпляр GameLauncher. Он наследуется от QObject и может испускать сигналы.
        self.worker = GameLauncher(nickname, profile_name, profile_data, MINECRAFT_DIRECTORY)

        # Соединяем сигналы
        self.worker.status_update.connect(self.log_output.append)
        self.worker.launch_finished.connect(self.on_launch_finished)

        # Создаем и запускаем стандартный поток Python, который вызовет метод run у нашего worker'а.
        # Сигналы будут безопасно переданы в основной поток GUI.
        self.thread = threading.Thread(target=self.worker.run, daemon=True)
        self.thread.start()

    def on_launch_finished(self):
        self.log_output.append("--- Готово ---")
        self.play_button.setEnabled(True)
        # Поток завершится сам, так как он daemon. Нам не нужно его останавливать.
        self.thread = None
        self.worker = None

    def analyze_current_profile(self):
        """Анализирует текущий профиль и предлагает оптимальные настройки."""
        profile_name = self.profiles_combo.currentText()
        if not profile_name:
            self.log_output.append("Сначала выберите профиль для анализа!")
            return

        mods_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name, "mods")
        mod_count = 0
        if os.path.isdir(mods_dir):
            mod_count = len([name for name in os.listdir(mods_dir) if name.endswith(".jar")])

        # Простая формула: 2ГБ база + 50МБ на каждый мод
        base_ram = 2048
        ram_per_mod = 50
        recommended_ram = base_ram + (mod_count * ram_per_mod)

        # Округляем до ближайших 512МБ для удобства
        recommended_ram = round(recommended_ram / 512) * 512
        
        # Убедимся, что мы не рекомендуем меньше базового значения
        recommended_ram = max(base_ram, recommended_ram)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Анализ профиля")
        msg_box.setText(
            f"Анализ профиля '{profile_name}':\n\n"
            f"Обнаружено модов: {mod_count}\n"
            f"Рекомендуемая RAM: {recommended_ram} МБ\n\n"
            "Хотите применить это значение к профилю?"
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            profiles = self.load_profiles_data()
            if profile_name in profiles:
                profiles[profile_name]['ram_mb'] = recommended_ram
                self.save_profiles_data(profiles)
                self.log_output.append(f"Профиль '{profile_name}' обновлен. Новое значение RAM: {recommended_ram} МБ.")

    def load_settings(self):
        """Загружает настройки из JSON-файла."""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Возвращаем настройки по умолчанию
            return {'show_snapshots': False, 'show_historical': False}

    def save_settings_data(self):
        """Сохраняет все настройки в JSON-файл."""
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def load_profiles_data(self):
        """Загружает данные о профилях из JSON-файла."""
        try:
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_profiles_data(self, profiles):
        """Сохраняет данные о профилях в JSON-файл."""
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=4)

    def populate_profiles_list(self):
        """Заполняет выпадающий список профилей."""
        self.profiles_combo.blockSignals(True)
        self.profiles_combo.clear()
        profiles = self.load_profiles_data()
        if profiles:
            self.profiles_combo.addItems(profiles.keys())
        self.profiles_combo.blockSignals(False)
        self.on_profile_selected(self.profiles_combo.currentText())

    def import_profiles(self):
        """Сканирует папку versions и предлагает импортировать новые профили."""
        self.log_output.append("Сканирование папки versions...")
        known_profiles = self.load_profiles_data().keys()
        
        # Получаем все папки из versions
        try:
            all_folders = [d for d in os.listdir(os.path.join(MINECRAFT_DIRECTORY, "versions")) if os.path.isdir(os.path.join(MINECRAFT_DIRECTORY, "versions", d))]
        except FileNotFoundError:
            all_folders = []

        # Исключаем официальные версии (которые содержат только цифры и точки)
        import re
        vanilla_pattern = re.compile(r"^\d+(\.\d+)*$")
        
        potential_profiles = [
            folder for folder in all_folders 
            if folder not in known_profiles and not vanilla_pattern.match(folder) and "-forge-" not in folder and "-fabric-" not in folder and "-neoforge-" not in folder
        ]

        if not potential_profiles:
            self.log_output.append("Новых сборок для импорта не найдено.")
            return

        for profile_name in potential_profiles:
            self.log_output.append(f"Найдена новая сборка: '{profile_name}'. Открытие диалога для настройки...")
            self.create_new_profile(prefilled_name=profile_name)


    def on_profile_selected(self, profile_name):
        """Обновляет список модов при выборе профиля."""
        self.populate_mods_list(profile_name)
        self.populate_resourcepacks_list(profile_name)
        self.populate_shaderpacks_list(profile_name)

    def create_new_profile(self, prefilled_name=""):
        """Открывает диалог для создания нового профиля."""
        # Если функция вызвана по сигналу от кнопки, prefilled_name может быть bool.
        # В этом случае мы должны использовать пустую строку.
        if not isinstance(prefilled_name, str):
            prefilled_name = ""
            
        dialog = ProfileDialog(self, profile_name=prefilled_name, settings=self.settings)
        if dialog.exec() and (profile_name := dialog.name_input.text()):

            profile_data = {
                "minecraft_version": dialog.version_combo.currentText(),
                "mod_loader": dialog.modloader_combo.currentText(),
                "ram_mb": dialog.ram_spinbox.value()
            }

            profiles = self.load_profiles_data()
            profiles[profile_name] = profile_data
            self.save_profiles_data(profiles)

            # Создаем папку для модов профиля
            profile_version_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name)
            os.makedirs(os.path.join(profile_version_dir, "mods"), exist_ok=True)
            os.makedirs(os.path.join(profile_version_dir, "resourcepacks"), exist_ok=True)
            os.makedirs(os.path.join(profile_version_dir, "shaderpacks"), exist_ok=True)


            self.populate_profiles_list()
            self.profiles_combo.setCurrentText(profile_name)

    def delete_profile(self):
        """Удаляет выбранный профиль."""
        profile_name = self.profiles_combo.currentText()
        if not profile_name:
            return

        profiles = self.load_profiles_data()
        if profile_name in profiles:
            del profiles[profile_name]
            self.save_profiles_data(profiles)

        profile_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name)
        if os.path.isdir(profile_dir):
            shutil.rmtree(profile_dir)

        self.populate_profiles_list()

    def populate_mods_list(self, profile_name):
        """Заполняет список модов для указанного профиля."""
        self._populate_list("mods", ".jar", self.mods_list_widget, profile_name)

    def add_mod(self):
        """Открывает диалог для добавления нового мода."""
        self._add_pack("mods", "Выбрать моды", "Jar-файлы (*.jar)", self.mods_list_widget, self.populate_mods_list)

    def remove_mod(self):
        """Удаляет выбранный мод."""
        self._remove_pack("mods", self.mods_list_widget)

    def populate_resourcepacks_list(self, profile_name):
        """Заполняет список текстур-паков для указанного профиля."""
        self._populate_list("resourcepacks", ".zip", self.resourcepacks_list_widget, profile_name)

    def add_resourcepack(self):
        """Открывает диалог для добавления нового текстур-пака."""
        self._add_pack("resourcepacks", "Выбрать текстур-паки", "Zip-архивы (*.zip)", self.resourcepacks_list_widget, self.populate_resourcepacks_list)

    def remove_resourcepack(self):
        """Удаляет выбранный текстур-пак."""
        self._remove_pack("resourcepacks", self.resourcepacks_list_widget)

    def populate_shaderpacks_list(self, profile_name):
        """Заполняет список шейдер-паков для указанного профиля."""
        self._populate_list("shaderpacks", ".zip", self.shaderpacks_list_widget, profile_name)

    def add_shaderpack(self):
        """Открывает диалог для добавления нового шейдер-пака."""
        self._add_pack("shaderpacks", "Выбрать шейдер-паки", "Zip-архивы (*.zip)", self.shaderpacks_list_widget, self.populate_shaderpacks_list)

    def remove_shaderpack(self):
        """Удаляет выбранный шейдер-пак."""
        self._remove_pack("shaderpacks", self.shaderpacks_list_widget)

    # --- Вспомогательные методы для управления файлами ---

    def _populate_list(self, pack_type, file_extension, list_widget, profile_name):
        """Общий метод для заполнения списков файлов (модов, текстур, шейдеров)."""
        list_widget.clear()
        if not profile_name:
            return

        pack_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name, pack_type)
        if not os.path.isdir(pack_dir):
            # Если папки нет, то и файлов в ней нет. Просто выходим.
            return
        
        for filename in os.listdir(pack_dir):
            if filename.endswith(file_extension):
                item = QListWidgetItem(filename)
                list_widget.addItem(item)

    def _add_pack(self, pack_type, dialog_title, file_filter, list_widget, populate_func):
        """Общий метод для добавления файлов (модов, текстур, шейдеров)."""
        profile_name = self.profiles_combo.currentText()
        if not profile_name:
            self.log_output.append("Сначала выберите или создайте профиль!")
            return

        filepaths, _ = QFileDialog.getOpenFileNames(self, dialog_title, "", file_filter)
        if not filepaths:
            return
        
        pack_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name, pack_type)
        os.makedirs(pack_dir, exist_ok=True)

        for filepath in filepaths:
            filename = os.path.basename(filepath)
            dest_path = os.path.join(pack_dir, filename)
            shutil.copy(filepath, dest_path)
        
        populate_func(profile_name)

    def _remove_pack(self, pack_type, list_widget):
        """Общий метод для удаления файлов."""
        profile_name = self.profiles_combo.currentText()
        selected_item = list_widget.currentItem()
        if not selected_item or not profile_name:
            return
        
        pack_dir = os.path.join(MINECRAFT_DIRECTORY, "versions", profile_name, pack_type)
        os.remove(os.path.join(pack_dir, selected_item.text()))
        list_widget.takeItem(list_widget.row(selected_item))


if __name__ == "__main__":
    # Проверяем, что директория существует
    if not os.path.exists(MINECRAFT_DIRECTORY):
        os.makedirs(MINECRAFT_DIRECTORY)
        
    app = QApplication(sys.argv)
    window = MainWindow()
    # Собираем стили из основного файла и всех плагинов
    final_styles = HACKER_STYLE + "\n" + window.plugin_manager.get_all_styles()
    app.setStyleSheet(final_styles)

    window.show()
    sys.exit(app.exec())
