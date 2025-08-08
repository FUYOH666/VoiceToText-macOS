"""
Модуль конфигурации для SuperWhisper
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any


class Config:
    """Класс для загрузки и управления конфигурацией приложения"""
    
    def __init__(self, config_path: str):
        """
        Инициализация конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации YAML
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Загружает конфигурацию из YAML файла
        
        Returns:
            Словарь с конфигурацией
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Файл конфигурации не найден: {self.config_path}"
                )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Конфигурация загружена из {self.config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def __getitem__(self, key: str) -> Any:
        """Доступ к параметрам конфигурации через индексы"""
        return self._config[key]
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации с возможностью задать default
        
        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию
            
        Returns:
            Значение конфигурации или default
        """
        return self._config.get(key, default)
    
    @property
    def app(self) -> Dict[str, Any]:
        """Конфигурация приложения"""
        return self._config["app"]
    
    @property
    def models(self) -> Dict[str, Any]:
        """Конфигурация моделей"""
        return self._config["models"]
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Конфигурация LLM"""
        return self._config["llm"]
    
    @property
    def audio(self) -> Dict[str, Any]:
        """Конфигурация аудио"""
        return self._config["audio"]
    
    @property
    def ui(self) -> Dict[str, Any]:
        """Конфигурация UI"""
        return self._config["ui"]
    
    @property
    def performance(self) -> Dict[str, Any]:
        """Конфигурация производительности"""
        return self._config["performance"] 