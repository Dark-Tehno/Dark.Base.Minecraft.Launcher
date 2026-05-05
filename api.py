from PyQt6.QtWidgets import QMainWindow, QWidget
from typing import Optional, Callable, Dict, Tuple, List
# Импортируем наш класс-помощник для type-hinting
from plugin_helpers import PluginUIHelper
from plugin_config import PluginConfig

class DBMLPlugin:
    """
    Базовый класс для плагинов Dark.Base.Minecraft.Launcher.
    Каждый плагин должен наследоваться от этого класса.
    """

    def __init__(self, main_window: QMainWindow, plugin_manager, helpers: PluginUIHelper, config: PluginConfig):
        """
        Инициализатор плагина.
        :param main_window: Экземпляр главного окна приложения (MainWindow).
        :param plugin_manager: Экземпляр менеджера плагинов.
        :param helpers: Экземпляр помощника для работы с UI.
        :param config: Экземпляр менеджера конфигурации для этого плагина.
        """
        self.main_window = main_window
        self.plugin_manager = plugin_manager
        self.helpers = helpers
        self.config = config
        self.name = self.__class__.__name__
        self.widgets = {} # Словарь для хранения ссылок на виджеты

    def get_styles(self) -> Optional[str]:
        """
        Позволяет плагину добавлять свои QSS стили.
        Возвращает строку со стилями, которая будет добавлена к основным.
        """
        return None

    def get_window_title(self) -> Optional[str]:
        """
        Позволяет плагину изменить заголовок главного окна лаунчера.
        Если несколько плагинов реализуют этот метод, будет использован заголовок от последнего загруженного плагина.
        """
        return None

    def get_window_icon(self) -> Optional[str]:
        """
        Позволяет плагину изменить иконку главного окна лаунчера.
        :return: Строка с путем к файлу иконки.
        """
        return None

    def modify_ui(self):
        """
        Вызывается после инициализации основного UI.
        Здесь плагины могут добавлять свои виджеты, кнопки, вкладки и т.д.
        Доступ к главному окну: self.main_window
        """
        pass

    def create_settings_page(self) -> Optional[Tuple[str, QWidget]]:
        """
        Позволяет плагину создать собственную страницу настроек.
        Эта страница будет добавлена как новая вкладка на основной вкладке "Настройки".

        :return: Кортеж (tuple) из двух элементов: (str: заголовок вкладки, QWidget: виджет с содержимым)
                 или None, если плагин не добавляет страницу настроек.
        """
        return None

    def get_widget_references(self) -> Optional[List[str]]:
        """
        Запрашивает у лаунчера прямые ссылки на ключевые виджеты.
        Имена виджетов будут использованы как ключи в словаре `self.widgets`.
        Это продвинутая функция, используйте с осторожностью.

        :return: Список (list) строк с `objectName` запрашиваемых виджетов.
                 Например: ["profiles_combo", "launch_tab", "mods_list_widget"]
        """
        return None

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

    def on_shutdown(self):
        """
        Вызывается при закрытии лаунчера.
        Используйте для сохранения данных или очистки.
        """
        pass

    def on_profile_changed(self, profile_name: str):
        """
        Вызывается при смене активного профиля в главном окне.
        """
        pass