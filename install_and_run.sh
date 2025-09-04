#!/bin/bash

# SuperWhisper - Установка и запуск
# Локальная диктовка для macOS

set -e

echo "🎤 SuperWhisper - Установка"
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
echo "📦 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi

# Активация окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "⬆️  Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "⬇️  Установка зависимостей..."
pip install -r requirements.txt

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p cache/punctuation
mkdir -p cache/transcriptions
mkdir -p vocabulary

# Проверка компонентов
echo "🧪 Проверка установки..."
python3.12 -c "
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

echo ""
echo "🎤 SuperWhisper готов к работе!"
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
    echo "🚀 Запуск SuperWhisper..."
    ./venv/bin/python superwhisper.py
fi
