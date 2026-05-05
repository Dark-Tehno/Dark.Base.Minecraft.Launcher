import os
import importlib.util
import sys
import inspect
from PyQt6.QtWidgets import QPushButton, QWidget, QTabWidget
from plugin_config import PluginConfig
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
        # 0. Передаем плагинам ссылки на виджеты, которые они запросили
        self._provide_widget_references()
        # 1. Позволяем плагинам добавить свои виджеты
        self.modify_all_ui()
        # 2. Применяем перехваты действий
        self._apply_action_overrides()
        # 3. Добавляем страницы настроек от плагинов
        self.create_settings_pages()

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
                            # Создаем для него персональный менеджер конфигурации
                            config_manager = PluginConfig(obj.__name__)
                            plugin_instance = obj(self.main_window, self, self.ui_helper, config_manager)
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

    def get_window_title(self) -> str | None:
        """
        Получает заголовок окна от последнего плагина, который его определяет.
        """
        title = None
        for plugin in self.plugins:
            plugin_title = plugin.get_window_title()
            if plugin_title:
                title = plugin_title
        return title
    
    def get_window_icon(self) -> str | None:
        """
        Получает иконку окна от последнего плагина, который ее определяет.
        """
        icon_path = None
        for plugin in self.plugins:
            plugin_icon_path = plugin.get_window_icon()
            if plugin_icon_path:
                icon_path = plugin_icon_path
        return icon_path
        

    def modify_all_ui(self):
        """Вызывает хук modify_ui для всех плагинов."""
        for plugin in self.plugins:
            plugin.modify_ui()

    def create_settings_pages(self):
        """Вызывает хук create_settings_page для всех плагинов и добавляет их вкладки."""
        for plugin in self.plugins:
            result = plugin.create_settings_page()
            if result:
                title, widget = result
                # Убедимся, что у нас есть вкладки настроек
                if title and widget and isinstance(self.main_window.settings_tabs, QTabWidget):
                    self.main_window.settings_tabs.addTab(widget, title)
                    print(f"INFO: Плагин '{plugin.name}' добавил страницу настроек '{title}'.")

    def run_pre_launch_hooks(self, launch_options: dict) -> dict:
        """Прогоняет опции запуска через все плагины."""
        options = launch_options
        for plugin in self.plugins:
            options = plugin.on_pre_launch(options)
        return options

    def run_shutdown_hooks(self):
        """Вызывает хук on_shutdown для всех плагинов."""
        print("Выполнение хуков завершения работы плагинов...")
        for plugin in self.plugins:
            plugin.on_shutdown()

    def run_profile_changed_hooks(self, profile_name: str):
        """Вызывает хук on_profile_changed для всех плагинов."""
        for plugin in self.plugins:
            plugin.on_profile_changed(profile_name)

    def _provide_widget_references(self):
        """
        Находит виджеты, запрошенные плагинами, и передает им ссылки.
        """
        # Собираем все запросы от всех плагинов, чтобы не искать виджеты по несколько раз
        all_requests = set()
        for plugin in self.plugins:
            requests = plugin.get_widget_references()
            if requests:
                all_requests.update(requests)

        # Находим все запрошенные виджеты
        found_widgets = {name: self.main_window.findChild(QWidget, name) for name in all_requests}

        # Передаем найденные виджеты в каждый плагин, который их запрашивал
        for plugin in self.plugins:
            requests = plugin.get_widget_references()
            if requests:
                for name in requests:
                    if found_widgets.get(name):
                        plugin.widgets[name] = found_widgets[name]

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
                    try:
                        button.clicked.disconnect()
                    except TypeError:
                        # Сигнал мог быть уже отключен, это не ошибка
                        pass
                    # Используем lambda, чтобы передать original_action в новый обработчик
                    button.clicked.connect(lambda checked=False, oa=original_action, na=new_action: na(oa))
                    overridden_buttons.add(button_name)
                    print(f"INFO: Действие кнопки '{button_name}' переопределено плагином '{plugin.name}'.")
                elif not button:
                    print(f"API Warning: Плагин '{plugin.name}' пытается переопределить несуществующую кнопку '{button_name}'.")
                elif not original_action:
                    print(f"API Warning: Для кнопки '{button_name}' не найдено оригинальное действие. Перехват невозможен.")