from PyQt6.QtWidgets import QMainWindow
from typing import Optional, Callable, Dict
# Импортируем наш класс-помощник для type-hinting
from plugin_helpers import PluginUIHelper

class DBMLPlugin:
    """
    Базовый класс для плагинов Dark.Base.Minecraft.Launcher.
    Каждый плагин должен наследоваться от этого класса.
    """

    def __init__(self, main_window: QMainWindow, plugin_manager, helpers: PluginUIHelper):
        """
        Инициализатор плагина.
        :param main_window: Экземпляр главного окна приложения (MainWindow).
        :param plugin_manager: Экземпляр менеджера плагинов.
        :param helpers: Экземпляр помощника для работы с UI.
        """
        self.main_window = main_window
        self.plugin_manager = plugin_manager
        self.helpers = helpers
        self.name = self.__class__.__name__

    def get_styles(self) -> Optional[str]:
        """
        Позволяет плагину добавлять свои QSS стили.
        Возвращает строку со стилями, которая будет добавлена к основным.
        """
        return None

    def modify_ui(self):
        """
        Вызывается после инициализации основного UI.
        Здесь плагины могут добавлять свои виджеты, кнопки, вкладки и т.д.
        Доступ к главному окну: self.main_window
        """
        pass

    def on_pre_launch(self, launch_options: dict) -> dict:
        """
        Вызывается прямо перед генерацией команды для запуска игры.
        Плагин может прочитать или изменить параметры запуска.
        :param launch_options: Словарь с опциями для minecraft_launcher_lib.
        :return: Измененный (или тот же) словарь с опциями.
        """
        return launch_options

    def get_action_overrides(self) -> Dict[str, Callable]:
        """
        Позволяет плагину переопределять действия кнопок.
        :return: Словарь, где:
                 - ключ (str) - это objectName кнопки, действие которой нужно перехватить.
                 - значение (Callable) - это новая функция-обработчик.
                 В новую функцию будет передан один аргумент: original_action (оригинальная функция).
                 Плагин сам решает, вызывать ли original_action.
        """
        return {}