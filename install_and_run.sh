#!/bin/bash

# VTT (VoiceToText) - Установка и запуск
# Локальная диктовка для macOS

set -e

echo "🎤 VTT (VoiceToText) - Установка"
echo "==========================="

# Проверка macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Это приложение работает только на macOS"
    exit 1
fi

# Проверка Python 3.12
if ! python3.12 --version >/dev/null 2>&1; then
    echo "❌ Требуется Python 3.12"
    echo "Установите через Homebrew: brew install python@3.12"
    exit 1
fi

# Создание виртуального окружения
echo "📦 Проверка виртуального окружения..."
if [ ! -d "venv" ]; then
    echo "Создание нового виртуального окружения..."
    python3.12 -m venv venv
else
    echo "Виртуальное окружение уже существует"
fi

# Активация окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "⬆️  Обновление pip..."
./venv/bin/python -m pip install --upgrade pip==25.2

# Установка зависимостей
echo "⬇️  Установка зависимостей..."
./venv/bin/python -m pip install -r requirements.txt

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p cache/punctuation
mkdir -p cache/transcriptions
mkdir -p vocabulary

# Проверка компонентов
echo "🧪 Проверка установки..."
./venv/bin/python -c "
import sys
print('✅ Python:', sys.version.split()[0])

try:
    import mlx_whisper
    print('✅ MLX Whisper готов')
except ImportError:
    print('❌ Ошибка MLX Whisper')

try:
    from src.config import Config
    print('✅ Конфигурация загружена')
except ImportError as e:
    print(f'❌ Ошибка конфигурации: {e}')
    sys.exit(1)
"

# Проверка accessibility
echo ""
echo "🔐 Проверка accessibility для горячих клавиш..."
./venv/bin/python -c "
import sys
try:
    import pynput.keyboard
    listener = pynput.keyboard.Listener(on_press=lambda k: None)
    listener.start()
    listener.stop()
    print('✅ Accessibility настроен корректно')
except Exception as e:
    print('⚠️  ВНИМАНИЕ: Проблемы с accessibility')
    print('   Горячие клавиши могут не работать')
    print('')
    print('   🔧 Для исправления:')
    print('   1. ./fix_accessibility.sh')
    print('   2. System Settings → Privacy & Security → Accessibility')
    print('   3. Добавьте Python в список доверенных приложений')
    print('')
    print('   📍 Найдите Python по пути: $(which python3)')
"

echo ""
echo "🎤 VTT (VoiceToText) готов к работе!"
echo "==============================="
echo "🚀 Для запуска:"
echo "   superwhisper    # Из любой директории"
echo ""
echo "⌨️  Управление:"
echo "   • Option + Space - запись/остановка"
echo "   • Иконка 🎤/🔴 в строке меню"
echo "   • Текст вставляется автоматически"
echo ""
echo "Запустить сейчас? (y/n)"
read -r run_now
if [[ "$run_now" =~ ^[Yy]$ ]]; then
    echo "🚀 Запуск VTT (VoiceToText)..."
    ./venv/bin/python superwhisper.py
fi
