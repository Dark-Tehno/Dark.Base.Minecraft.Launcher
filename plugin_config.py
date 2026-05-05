import os
import json
import sys

class PluginConfig:
    """
    Управляет сохранением и загрузкой настроек для одного плагина.
    Каждый плагин получает свой собственный JSON-файл в папке plugins/config.
    """
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)

        self.config_dir = os.path.join(base_path, "plugins", "config")
        os.makedirs(self.config_dir, exist_ok=True)

        self.config_file = os.path.join(self.config_dir, f"{self.plugin_name}.json")
        self.settings = self._load()

    def _load(self) -> dict:
        """Загружает настройки из файла."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        """Сохраняет текущие настройки в файл."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key: str, default=None):
        """
        Получает значение настройки по ключу.
        :param key: Ключ настройки.
        :param default: Значение по умолчанию, если ключ не найден.
        :return: Значение настройки.
        """
        return self.settings.get(key, default)

    def set(self, key: str, value):
        """
        Устанавливает значение настройки и немедленно сохраняет его в файл.
        :param key: Ключ настройки.
        :param value: Новое значение.
        """
        self.settings[key] = value
        self._save()