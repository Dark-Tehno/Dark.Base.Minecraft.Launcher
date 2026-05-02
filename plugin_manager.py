import os
import importlib.util
import sys
import inspect
from PyQt6.QtWidgets import QPushButton
from api import DBMLPlugin, PluginUIHelper
from plugin_helpers import PluginUIHelper

class PluginManager:
    """
    Управляет загрузкой плагинов и вызовом их хуков.
    """
    def __init__(self, main_window):
        # Создаем один экземпляр помощника, который будем передавать всем плагинам
        self.ui_helper = PluginUIHelper(main_window)
        self.main_window = main_window
        self.plugins = []
        self.load_plugins()
    
    def initialize_plugins(self):
        """Выполняет все действия по инициализации плагинов после создания UI."""
        # 1. Позволяем плагинам добавить свои виджеты
        self.modify_all_ui()
        # 2. Применяем перехваты действий
        self._apply_action_overrides()

    def load_plugins(self):
        """
        Находит и загружает плагины из папки /plugins.
        """
        # Определяем базовый путь. Это будет работать как в исходниках, так и в скомпилированном .exe
        if getattr(sys, 'frozen', False):
            # Если приложение "заморожено" (скомпилировано в exe)
            base_path = os.path.dirname(sys.executable)
        else:
            # Если запускается из исходников
            base_path = os.path.dirname(__file__)

        plugins_dir = os.path.join(base_path, "plugins")
        if not os.path.isdir(plugins_dir):
            os.makedirs(plugins_dir) # Создаем папку, если ее нет

        print("Загрузка плагинов...")
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(plugins_dir, filename)
                module_name = f"plugins.{filename[:-3]}"

                try:
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, DBMLPlugin) and obj is not DBMLPlugin:
                            # Нашли класс плагина, создаем его экземпляр
                            plugin_instance = obj(self.main_window, self, self.ui_helper)
                            self.plugins.append(plugin_instance)
                            print(f"  - Плагин '{plugin_instance.name}' успешно загружен.")
                except Exception as e:
                    print(f"Ошибка при загрузке плагина из файла {filename}: {e}")

    def get_all_styles(self) -> str:
        """Собирает стили со всех плагинов."""
        all_styles = []
        for plugin in self.plugins:
            styles = plugin.get_styles()
            if styles:
                all_styles.append(styles)
        return "\n".join(all_styles)

    def modify_all_ui(self):
        """Вызывает хук modify_ui для всех плагинов."""
        for plugin in self.plugins:
            plugin.modify_ui()

    def run_pre_launch_hooks(self, launch_options: dict) -> dict:
        """Прогоняет опции запуска через все плагины."""
        options = launch_options
        for plugin in self.plugins:
            options = plugin.on_pre_launch(options)
        return options

    def _apply_action_overrides(self):
        """
        Ищет плагины, которые хотят переопределить ключевые действия,
        и применяет их.
        """
        overridden_buttons = set()

        for plugin in self.plugins:
            overrides = plugin.get_action_overrides()
            for button_name, new_action in overrides.items():
                if button_name in overridden_buttons:
                    print(f"API Warning: Действие для кнопки '{button_name}' уже переопределено. Запрос от плагина '{plugin.name}' игнорируется.")
                    continue

                button = self.main_window.findChild(QPushButton, button_name)
                original_action = self.main_window.original_actions.get(button_name)

                if button and original_action:
                    button.clicked.disconnect()
                    # Используем lambda, чтобы передать original_action в новый обработчик
                    button.clicked.connect(lambda checked=False, oa=original_action, na=new_action: na(oa))
                    overridden_buttons.add(button_name)
                    print(f"INFO: Действие кнопки '{button_name}' переопределено плагином '{plugin.name}'.")
                elif not button:
                    print(f"API Warning: Плагин '{plugin.name}' пытается переопределить несуществующую кнопку '{button_name}'.")
                elif not original_action:
                    print(f"API Warning: Для кнопки '{button_name}' не найдено оригинальное действие. Перехват невозможен.")