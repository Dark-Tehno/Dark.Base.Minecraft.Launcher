# Документация по созданию плагинов для Dark.Base.Minecraft.Launcher (DBML)

## Введение

Система плагинов DBML позволяет расширять функциональность и изменять внешний вид лаунчера, не затрагивая его основной код. Вы можете добавлять новые кнопки, изменять логику существующих, кастомизировать стили и многое другое.

## Быстрый старт

1.  Создайте новый Python-файл (например, `my_cool_plugin.py`) в папке `plugins`.
2.  В этом файле создайте класс, унаследованный от `DBMLPlugin`.
3.  Реализуйте один или несколько "хуков" (методов API) для добавления вашей логики.

```python
# plugins/my_cool_plugin.py
from api import DBMLPlugin

class MyCoolPlugin(DBMLPlugin):
    def modify_ui(self):
        print(f"[{self.name}] Мой плагин загружен и готов менять UI!")
        self.helpers.show_info_message("Привет!", "Мой крутой плагин успешно загружен!")
```

## Основы API

### Класс `DBMLPlugin`

Каждый плагин должен наследоваться от базового класса `api.DBMLPlugin`. При инициализации ваш плагин получает три важных объекта:

-   `self.main_window`: Экземпляр главного окна `MainWindow` (PyQt6). Дает полный доступ ко всему UI, но рекомендуется использовать `helpers`.
-   `self.plugin_manager`: Экземпляр менеджера плагинов.
-   `self.helpers`: Экземпляр `PluginUIHelper`, предоставляющий безопасные и простые методы для работы с UI. **Это рекомендуемый способ взаимодействия с интерфейсом.**

### Помощник `PluginUIHelper` (`self.helpers`)

Этот объект упрощает взаимодействие с UI.

-   `add_button_to_launch_area(text: str, on_click: callable)`: Добавляет кнопку в левую колонку на вкладке "Запуск".
-   `add_main_tab(title: str) -> QWidget`: Добавляет новую основную вкладку (рядом с "Запуск" и "Настройки") и возвращает ее виджет для наполнения.
-   `show_info_message(title: str, text: str)`: Показывает простое информационное сообщение.

## Хуки (Hooks) API

Хуки — это методы класса `DBMLPlugin`, которые вы можете переопределить в своем плагине, чтобы встроиться в работу лаунчера.

---

### `get_styles() -> Optional[str]`

Позволяет добавить кастомные стили QSS. Стили плагина будут добавлены к основным стилям лаунчера. Вы можете изменять внешний вид как общих элементов, так и конкретных виджетов по их `objectName`.

**Пример:**
```python
def get_styles(self) -> str:
    # Делаем кнопку "Играть" оранжевой
    return """
        QPushButton#play_button {
            background-color: #ff8c00;
            color: white;
        }
    """
```

---

### `modify_ui()`

Вызывается после того, как основной интерфейс лаунчера создан. Здесь вы можете добавлять свои кнопки, вкладки и другие элементы. Используйте `self.helpers` для этого.

**Пример:**
```python
def modify_ui(self):
    # Добавляем кнопку, которая показывает сообщение при нажатии
    self.helpers.add_button_to_launch_area(
        text="Показать инфо",
        on_click=self.show_my_message
    )

def show_my_message(self):
    self.helpers.show_info_message("Инфо", "Эта кнопка добавлена плагином!")
```

---

### `on_pre_launch(launch_options: dict) -> dict`

Вызывается прямо перед запуском игры. Позволяет прочитать и изменить параметры запуска.

**Пример:**
```python
def on_pre_launch(self, launch_options: dict) -> dict:
    # Добавляем кастомный JVM-аргумент
    print(f"[{self.name}] Добавляю JVM-аргумент.")
    launch_options['jvmArguments'].append("-Dmy.custom.property=true")
    return launch_options
```

---

### `get_action_overrides() -> Dict[str, Callable]`

Самый мощный хук. Позволяет полностью переопределить действие стандартных кнопок. Вы должны вернуть словарь, где ключ — это `objectName` кнопки, а значение — ваша новая функция-обработчик.

Ваша функция-обработчик получит один аргумент — `original_action`, который является оригинальной функцией кнопки. Вы сами решаете, вызывать ее или нет.

**Пример:**
```python
from PyQt6.QtWidgets import QMessageBox

def get_action_overrides(self) -> dict:
    return {
        "play_button": self.override_play_button
    }

def override_play_button(self, original_action):
    # Задаем вопрос перед запуском
    reply = QMessageBox.question(self.main_window, 'Подтверждение', "Вы уверены, что хотите запустить игру?")
    if reply == QMessageBox.StandardButton.Yes:
        # Если пользователь согласен, вызываем оригинальное действие
        original_action()
```
