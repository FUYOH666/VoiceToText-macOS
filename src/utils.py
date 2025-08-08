"""
Утилитарные функции для SuperWhisper
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Настройка системы логирования
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу для записи логов (необязательно)
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройка основного логгера
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Добавляем обработчик в root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # Файловый вывод (если указан)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    
    # Отключаем избыточное логирование библиотек
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def format_duration(seconds: float) -> str:
    """
    Форматирует продолжительность в читаемый вид
    
    Args:
        seconds: Продолжительность в секундах
        
    Returns:
        Отформатированная строка времени
    """
    if seconds < 60:
        return f"{seconds:.1f}с"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}м {secs}с"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}ч {minutes}м"


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Символы, недопустимые в именах файлов
    forbidden_chars = '<>:"/\\|?*'
    
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    
    # Убираем множественные пробелы и подчеркивания
    filename = ' '.join(filename.split())
    filename = '_'.join(filename.split('_'))
    
    return filename.strip()


def ensure_dir(path: Path) -> Path:
    """
    Создает директорию если она не существует
    
    Args:
        path: Путь к директории
        
    Returns:
        Путь к созданной директории
    """
    path.mkdir(parents=True, exist_ok=True)
    return path 