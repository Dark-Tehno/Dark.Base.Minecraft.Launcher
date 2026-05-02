# Dark.Base.Minecraft.Launcher (DBML)

![GitHub repo size](https://img.shields.io/github/repo-size/Dark-Tehno/Dark.Base.Minecraft.Launcher?style=for-the-badge&color=00ff41)
![GitHub language count](https://img.shields.io/github/languages/count/Dark-Tehno/Dark.Base.Minecraft.Launcher?style=for-the-badge&color=00ff41)
![GitHub top language](https://img.shields.io/github/languages/top/Dark-Tehno/Dark.Base.Minecraft.Launcher?style=for-the-badge&color=00ff41)

**DBML** — это базовый, но мощный Minecraft-лаунчер с открытым исходным кодом, созданный на Python и PyQt6. Его ключевая особенность — гибкая система плагинов, которая позволяет кастомизировать и расширять функциональность, не изменяя основной код.

Проект задуман как "Chromium для лаунчеров": надежная основа, на которой каждый может построить свой идеальный лаунчер.

---

## 🚀 Основные возможности

*   **Оффлайн-аутентификация**: Вход в игру по любому никнейму без учетной записи Mojang/Microsoft.
*   **Управление профилями**: Создавайте изолированные сборки с разными версиями Minecraft, модлоадерами и настройками.
*   **Поддержка модлоадеров**: Автоматическая установка `Forge`, `Fabric` и `NeoForge`.
*   **Менеджер файлов**: Удобное добавление и удаление модов, текстур-паков и шейдеров для каждого профиля.
*   **Анализатор сборок**: Инструмент для рекомендации оптимального количества RAM на основе числа установленных модов.
*   **Кастомизируемый интерфейс**: "Хакерская" тема в стиле ретро-терминалов.
*   **Мощный API для плагинов**: Расширяйте функциональность с помощью простого и хорошо документированного API.

## ⚙️ Установка и запуск

Для работы лаунчера требуется Python 3.8 или новее.

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/Dark-Tehno/Dark.Base.Minecraft.Launcher.git
    cd Dark.Base.Minecraft.Launcher
    ```

2.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Запустите лаунчер:**
    ```bash
    python gui.py
    ```

## 🔌 Разработка плагинов

Хотите добавить новую функцию или изменить поведение лаунчера? Это легко! Вся логика расширений вынесена в плагины.

Подробная документация по созданию плагинов находится в специальном файле:

➡️ [**Документация по API плагинов**](https://github.com/Dark-Tehno/Dark.Base.Minecraft.Launcher/blob/main/API.md)

## 🤝 Участие в разработке (Contributing)

Мы приветствуем любой вклад в развитие проекта! Если у вас есть идеи, предложения или вы нашли ошибку, пожалуйста, создайте `Issue` или `Pull Request`.

1.  Сделайте форк проекта.
2.  Создайте новую ветку (`git checkout -b feature/AmazingFeature`).
3.  Внесите свои изменения.
4.  Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`).
5.  Отправьте изменения в свою ветку (`git push origin feature/AmazingFeature`).
6.  Откройте Pull Request.

## 📄 Лицензия

Проект распространяется под лицензией Apache License 2.0 Подробности смотрите в файле `LICENSE`.