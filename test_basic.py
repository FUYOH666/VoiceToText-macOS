#!/usr/bin/env python3
"""
Базовые тесты для SuperWhisper Local
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestSuperWhisperComponents(unittest.TestCase):
    """Тесты основных компонентов"""
    
    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        from src.config import Config
        
        # Тест загрузки существующего файла
        if os.path.exists('config.yaml'):
            config = Config('config.yaml')
            self.assertIsNotNone(config.app)
            self.assertIsNotNone(config.models)
    
    def test_hotkey_manager_init(self):
        """Тест инициализации менеджера горячих клавиш"""
        from src.hotkey_manager import HotkeyManager
        
        hotkey_manager = HotkeyManager()
        self.assertIsNotNone(hotkey_manager.logger)
        self.assertFalse(hotkey_manager.is_running)
    
    def test_notification_service(self):
        """Тест сервиса уведомлений"""
        from src.notification_service import NotificationService
        
        notification_service = NotificationService()
        self.assertIsNotNone(notification_service.logger)
    
    def test_punctuation_service_basic(self):
        """Тест базовой пунктуации"""
        from src.punctuation_service import PunctuationService
        
        # Мокаем конфиг
        mock_config = Mock()
        mock_config.models = {
            "punctuation": {"model_name": "test"}
        }
        
        service = PunctuationService(mock_config)
        
        # Тест базовой обработки
        result = service._restore_basic("привет как дела")
        self.assertTrue(result[0].isupper())  # Первая буква заглавная
        self.assertTrue(result.endswith('.'))  # Точка в конце
    
    def test_audio_utils(self):
        """Тест утилит для аудио"""
        from src.utils import setup_logging
        
        # Тест настройки логирования
        setup_logging()
        # Если не вызывает исключений - тест пройден
        self.assertTrue(True)

class TestSystemRequirements(unittest.TestCase):
    """Тесты системных требований"""
    
    def test_python_version(self):
        """Проверка версии Python"""
        self.assertGreaterEqual(sys.version_info[:2], (3, 11))
    
    def test_required_packages(self):
        """Проверка наличия основных пакетов"""
        try:
            import torch
            import numpy
            import yaml
            import pyperclip
            import pynput
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Отсутствует обязательный пакет: {e}")

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов SuperWhisper Local")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestSystemRequirements))
    suite.addTests(loader.loadTestsFromTestCase(TestSuperWhisperComponents))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ Все тесты пройдены!")
        return True
    else:
        print("\n❌ Некоторые тесты не прошли")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 