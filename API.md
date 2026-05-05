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

Каждый плагин должен наследоваться от базового класса `api.DBMLPlugin`. При инициализации ваш плагин получает несколько важных объектов:

-   `self.main_window`: Экземпляр главного окна `MainWindow` (PyQt6). Дает полный доступ ко всему UI, но рекомендуется использовать `helpers`.
-   `self.plugin_manager`: Экземпляр менеджера плагинов.
-   `self.helpers`: Экземпляр `PluginUIHelper`, предоставляющий безопасные и простые методы для работы с UI. **Это рекомендуемый способ взаимодействия с интерфейсом.**
-   `self.config`: Экземпляр `PluginConfig`, который позволяет вашему плагину сохранять и загружать собственные настройки.
-   `self.widgets`: Словарь, в который будут помещены ссылки на виджеты, запрошенные через хук `get_widget_references()`.
-   `self.name`: Имя вашего плагина (имя класса).


При этом в `self.widgets` будут помещены ссылки на виджеты, которые плагин запросит через хук `get_widget_references()`.


### Помощник `PluginUIHelper` (`self.helpers`)

Этот объект-помощник предоставляет набор безопасных и простых в использовании методов для взаимодействия с основным интерфейсом лаунчера. **Это рекомендуемый способ изменения UI.**

---

#### `add_button_to_launch_area(text: str, on_click: callable)`

Добавляет кнопку в левую колонку на вкладке "Запуск", под списком профилей.

| Параметр | Тип        | Описание                                      |
| :------- | :--------- | :-------------------------------------------- |
| `text`   | `str`      | Текст, который будет отображаться на кнопке.   |
| `on_click` | `callable` | Функция, которая будет вызвана при нажатии. |

**Пример:**
```python
def modify_ui(self):
    self.helpers.add_button_to_launch_area(
        text="Показать инфо",
        on_click=self.show_my_message
    )

def show_my_message(self):
    self.helpers.show_info_message("Инфо", "Эта кнопка добавлена плагином!")
```

---

#### `add_main_tab(title: str) -> QWidget`

Добавляет новую основную вкладку в лаунчер (рядом с "Запуск" и "Настройки").

| Параметр | Тип   | Описание                  |
| :------- | :---- | :------------------------ |
| `title`  | `str` | Заголовок новой вкладки. |

**Возвращает:**
-   **Тип:** `QWidget`
-   **Описание:** Виджет, который является содержимым новой вкладки. Вы можете добавлять свои элементы в этот виджет, используя, например, `QVBoxLayout`.

**Пример:**
```python
from PyQt6.QtWidgets import QVBoxLayout, QLabel

def modify_ui(self):
    about_tab = self.helpers.add_main_tab("О плагине")
    layout = QVBoxLayout(about_tab)
    layout.addWidget(QLabel("Это демонстрационный плагин для DBML!"))
    layout.addStretch()
```

---

#### `show_info_message(title: str, text: str)`

Показывает стандартное информационное сообщение (диалоговое окно).

| Параметр | Тип   | Описание                     |
| :------- | :---- | :--------------------------- |
| `title`  | `str` | Заголовок окна сообщения.    |
| `text`   | `str` | Основной текст сообщения.    |

---

#### `log_message(text: str)`

Добавляет текстовое сообщение в виджет лога на вкладке "Запуск". Удобно для отладки и информирования пользователя о действиях плагина.

| Параметр | Тип   | Описание                  |
| :------- | :---- | :------------------------ |
| `text`   | `str` | Текст сообщения для лога. |

Хуки — это методы класса `DBMLPlugin`, которые вы можете переопределить в своем плагине, чтобы встроиться в работу лаунчера.

---

### Управление конфигурацией (`self.config`)

Каждый плагин получает собственный менеджер конфигурации, доступный через `self.config`. Он позволяет легко сохранять и загружать данные в персональный JSON-файл плагина (`plugins/config/ИмяПлагина.json`).

#### `self.config.get(key: str, default=None)`
Получает значение настройки по ключу.

| Параметр  | Тип   | Описание                                     |
| :-------- | :---- | :------------------------------------------- |
| `key`     | `str` | Ключ настройки.                              |
| `default` | `any` | Значение по умолчанию, если ключ не найден. |

#### `self.config.set(key: str, value)`
Устанавливает значение настройки и немедленно сохраняет его в файл.

| Параметр | Тип   | Описание          |
| :------- | :---- | :---------------- |
| `key`    | `str` | Ключ настройки.   |
| `value`  | `any` | Новое значение.   |

**Пример использования в `create_settings_page`:**
```python
def create_settings_page(self):
    page = QWidget()
    layout = QFormLayout(page)
    api_key_input = QLineEdit()
    # Загружаем сохраненное значение при создании страницы
    api_key_input.setText(self.config.get("api_key", ""))
    # Сохраняем значение при его изменении
    api_key_input.textChanged.connect(lambda text: self.config.set("api_key", text))
    layout.addRow("Ваш API ключ:", api_key_input)
    return ("Мой плагин", page)
```

---

### `get_styles() -> Optional[str]`

Позволяет добавить кастомные стили QSS. Стили плагина будут добавлены к основным стилям лаунчера. Вы можете изменять внешний вид как общих элементов, так и конкретных виджетов по их `objectName`.

**Возвращает:**
-   **Тип:** `str` или `None`
-   **Описание:** Строка, содержащая валидные QSS-стили.

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

### `get_window_title() -> Optional[str]`

Позволяет плагину изменить заголовок главного окна лаунчера. Если несколько плагинов реализуют этот хук, будет использован заголовок от последнего загруженного плагина.

**Возвращает:**
-   **Тип:** `str` или `None`
-   **Описание:** Новая строка для заголовка окна.

**Пример:**
```python
def get_window_title(self) -> str:
    # Устанавливаем свой заголовок
    return "My Awesome Custom Launcher"
```

---

### `get_window_icon() -> Optional[str]`

Позволяет плагину изменить иконку главного окна лаунчера. Если несколько плагинов реализуют этот хук, будет использована иконка от последнего загруженного плагина.

**Возвращает:**
-   **Тип:** `str` или `None`
-   **Описание:** Путь к файлу иконки (например, `.ico`, `.png`).

**Пример:**
```python
import os

def get_window_icon(self) -> str:
    # Устанавливаем свою иконку из папки плагина
    return os.path.join(os.path.dirname(__file__), "my_icon.png")
```
---

### `modify_ui()`

Вызывается после того, как основной интерфейс лаунчера создан. Это основное место для добавления виджетов, вкладок и кнопок с помощью `self.helpers`.

---

### `create_settings_page() -> Optional[Tuple[str, QWidget]]`

Позволяет плагину создать собственную страницу настроек. Эта страница будет добавлена как новая под-вкладка на основной вкладке "Настройки".

**Возвращает:**
-   **Тип:** `Tuple[str, QWidget]` или `None`
-   **Описание:** Кортеж из двух элементов:
    1.  `str`: Заголовок для новой вкладки настроек.
    2.  `QWidget`: Виджет-контейнер со всеми элементами настроек вашего плагина.

**Пример (см. также пример для `self.config`):**
```python
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit

def create_settings_page(self):
    # Создаем виджет-контейнер для нашей страницы
    page_widget = QWidget()
    layout = QFormLayout(page_widget)

    # Добавляем элементы настроек
    my_setting_input = QLineEdit()
    my_setting_input.setPlaceholderText("Введите значение...")
    layout.addRow("Настройка 1:", my_setting_input)
    layout.addRow("Настройка 2:", QLineEdit("Другое значение"))

    return ("Мой плагин", page_widget)
```

---

### `get_widget_references() -> Optional[List[str]]` (для продвинутых)

Позволяет плагину запросить у лаунчера прямые ссылки на любые виджеты, у которых задан `objectName`. Это открывает практически безграничные возможности для кастомизации. После успешного выполнения хука, ссылки на виджеты будут доступны в словаре `self.widgets`.

**Используйте с осторожностью!** Прямое манипулирование виджетами может нарушить работу лаунчера, если не знать, что вы делаете.

**Возвращает:**
-   **Тип:** `List[str]` или `None`
-   **Описание:** Список строк с `objectName` запрашиваемых виджетов.

**Примеры доступных `objectName`:**
-   `"play_button"`: `QPushButton` - кнопка "Играть".
-   `"profiles_combo"`: `QComboBox` - выпадающий список профилей.
-   `"launch_tab"`: `QWidget` - основная вкладка "Запуск".
-   `"settings_tabs"`: `QTabWidget` - контейнер вкладок на странице "Настройки".
-   `"mods_list_widget"`, `"resourcepacks_list_widget"`, `"shaderpacks_list_widget"`: `QListWidget` для списков файлов.

**Пример: Замена кнопки "Играть" на иконку и отслеживание смены профиля**
```python
import os
from PyQt6.QtGui import QIcon

def get_widget_references(self) -> list[str]:
    # Запрашиваем доступ к списку профилей и кнопке "Играть"
    return ["profiles_combo", "play_button"]

def modify_ui(self):
    # Теперь мы можем работать с этими виджетами напрямую
    # 1. Меняем кнопку "Играть"
    if play_button := self.widgets.get("play_button"):
        play_button = self.widgets["play_button"]
        play_button.setText("") # Убираем текст с кнопки
        icon_path = os.path.join(os.path.dirname(__file__), "my_play_icon.png")
        play_button.setIcon(QIcon(icon_path))
        # play_button.setIconSize(play_button.sizeHint() * 1.2) # Можно сделать иконку побольше
```

---

### `on_pre_launch(launch_options: dict) -> dict`

Вызывается прямо перед запуском игры. Позволяет прочитать и/или изменить параметры запуска, которые будут переданы в `minecraft-launcher-lib`.

| Параметр         | Тип    | Описание                                                              |
| :--------------- | :----- | :-------------------------------------------------------------------- |
| `launch_options` | `dict` | Словарь с опциями запуска (версия, RAM, jvm-аргументы и т.д.). |

**Возвращает:**
-   **Тип:** `dict`
-   **Описание:** Измененный (или тот же) словарь с опциями запуска.

**Пример: Добавление JVM-аргумента**
```python
def on_pre_launch(self, launch_options: dict) -> dict:
    # Добавляем кастомный JVM-аргумент
    print(f"[{self.name}] Добавляю JVM-аргумент.")
    if 'jvmArguments' not in launch_options:
        launch_options['jvmArguments'] = []
    launch_options['jvmArguments'].append("-Dmy.plugin.property=true")
    return launch_options
```

---

### `on_profile_changed(profile_name: str)`

Вызывается каждый раз, когда пользователь выбирает другой профиль в выпадающем списке.

| Параметр       | Тип   | Описание                                |
| :------------- | :---- | :-------------------------------------- |
| `profile_name` | `str` | Имя нового выбранного профиля. |

**Пример:**
```python
def on_profile_changed(self, profile_name: str):
    message = f"Плагин '{self.name}' зафиксировал смену профиля на: {profile_name}"
    self.helpers.log_message(message)
```

---

### `on_shutdown()`

Вызывается при закрытии лаунчера. Используйте этот хук для сохранения данных, очистки временных файлов или завершения фоновых процессов.

**Пример:**
```python
def on_shutdown(self):
    # Сохраняем какие-то финальные данные или просто логируем
    print(f"Плагин '{self.name}' завершает работу. Сохраняем данные...")
```

---

### `get_action_overrides() -> Dict[str, Callable]`

Позволяет полностью переопределить действие стандартных кнопок лаунчера.

**Возвращает:**
-   **Тип:** `Dict[str, Callable]`
-   **Описание:** Словарь, где:
    -   **ключ** (`str`) - это `objectName` кнопки, действие которой нужно перехватить (например, `"play_button"`).
    -   **значение** (`Callable`) - это ваша новая функция-обработчик.

Ваша функция-обработчик получит один аргумент — `original_action`, который является оригинальным обработчиком кнопки. Вы сами решаете, вызывать его или нет.

**Доступные `objectName` для перехвата:**
-   `"play_button"`: Кнопка "Играть".
-   `"analyze_profile_button"`: Кнопка "Анализ".
-   `"new_profile_button"`: Кнопка "Создать" профиль.
-   `"delete_profile_button"`: Кнопка "Удалить" профиль.
-   `"import_profile_button"`: Кнопка "Импорт" профилей.
-   `"add_mod_button"`, `"remove_mod_button"`: Кнопки управления модами.
-   `"add_resourcepack_button"`, `"remove_resourcepack_button"`: Кнопки управления текстурами.
-   `"add_shaderpack_button"`, `"remove_shaderpack_button"`: Кнопки управления шейдерами.

**Пример: Запрос подтверждения перед запуском игры**
```python
from PyQt6.QtWidgets import QMessageBox

def get_action_overrides(self) -> dict:
    return {
        "play_button": self.confirm_before_play
    }

def confirm_before_play(self, original_action):
    # Задаем вопрос перед запуском
    reply = QMessageBox.question(self.main_window, 'Подтверждение', "Вы уверены, что хотите запустить игру?")
    if reply == QMessageBox.StandardButton.Yes:
        # Если пользователь согласен, вызываем оригинальное действие
        original_action()
```
