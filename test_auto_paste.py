#!/usr/bin/env python3
"""
Тест простой автовставки
"""

import os
import sys
import time

# Добавляем src в PATH
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from src.config import Config
from src.auto_paste import AutoPasteService


def test_auto_paste():
    """Тестирует простую автовставку"""
    print("🧪 Тест простой автовставки")
    
    try:
        # Загружаем конфигурацию
        config = Config("config.yaml")
        
        # Создаём сервис автовставки
        auto_paste_service = AutoPasteService(config)
        
        # Тестовый текст
        test_text = "Привет! Это тест автовставки для SuperWhisper Simple."
        
        print(f"💬 Тестовый текст: '{test_text}'")
        print("⏰ Подготовьтесь - через 3 секунды текст будет вставлен...")
        print("📝 Установите курсор в любое текстовое поле!")
        
        # Ждём 3 секунды
        for i in range(3, 0, -1):
            print(f"⏳ {i}...")
            time.sleep(1)
        
        print("🚀 Вставляем текст...")
        
        # Вставляем текст
        success = auto_paste_service.paste_text(test_text)
        
        if success:
            print("✅ Автовставка выполнена успешно!")
        else:
            print("❌ Автовставка не удалась")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")


if __name__ == "__main__":
    test_auto_paste() 