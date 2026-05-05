from PyQt6.QtWidgets import QPushButton, QMessageBox, QWidget, QVBoxLayout

class PluginUIHelper:
    """
    Предоставляет упрощенные, высокоуровневые методы для взаимодействия
    плагинов с пользовательским интерфейсом лаунчера.
    Экземпляр этого класса передается в каждый плагин.
    """
    def __init__(self, main_window):
        self.main_window = main_window

    def add_button_to_launch_area(self, text: str, on_click: callable):
        """
        Добавляет кнопку в область настроек запуска (левая колонка).

        :param text: Текст на кнопке.
        :param on_click: Функция, которая будет вызвана при нажатии.
        """
        button = QPushButton(text)
        button.clicked.connect(on_click)
        
        # Находим layout по имени объекта, которое мы задали в gui.py
        launch_settings_layout = self.main_window.findChild(QVBoxLayout, "launch_settings_layout")
        if launch_settings_layout:
            launch_settings_layout.addWidget(button)
        else:
            # Это сообщение поможет разработчикам плагинов, если что-то пойдет не так
            print("API Error: Не удалось найти 'launch_settings_layout' для добавления кнопки.")

    def add_main_tab(self, title: str) -> QWidget:
        """
        Добавляет новую основную вкладку в лаунчер (рядом с "Запуск" и "Настройки").

        :param title: Заголовок вкладки.
        :return: QWidget, который является содержимым новой вкладки.
                 Плагин может добавлять свои элементы в этот виджет, используя, например, QVBoxLayout.
        """
        new_tab_content = QWidget()
        self.main_window.tabs.addTab(new_tab_content, title)
        return new_tab_content

    def show_info_message(self, title: str, text: str):
        """
        Показывает простое информационное сообщение.

        :param title: Заголовок окна сообщения.
        :param text: Текст сообщения.
        """
        QMessageBox.information(self.main_window, title, text)

    def log_message(self, text: str):
        """
        Добавляет сообщение в основной лог на вкладке "Запуск".

        :param text: Текст сообщения для лога.
        """
        if hasattr(self.main_window, 'log_output'):
            self.main_window.log_output.append(text)