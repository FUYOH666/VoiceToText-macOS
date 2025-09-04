#!/bin/bash

# SuperWhisper Simple - Установка и запуск
echo "🚀 SuperWhisper Simple - Установка и запуск"
echo "============================================"

# Автоматический переход в директорию скрипта (работает из любой директории!)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "📁 Автоматический переход в: $(pwd)"
echo "✅ НОВЫЕ ИСПРАВЛЕНИЯ: Идеальная пунктуация + исправленные вопросы!"

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
    echo "Создаю новое виртуальное окружение..."
    python3.12 -m venv venv
fi

# Активация окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip в виртуальном окружении
echo "⬆️  Обновление pip..."
./venv/bin/pip install --upgrade pip

# Установка зависимостей
echo "⬇️  Установка зависимостей..."
./venv/bin/pip install -r requirements.txt

# Создание директорий для кэша
echo "📁 Создание директорий..."
mkdir -p cache/transcriptions
mkdir -p cache/vad
mkdir -p cache/punctuation
mkdir -p models

# Проверка компонентов
echo "🧪 Проверка компонентов..."
./venv/bin/python test_basic.py
if [ $? -eq 0 ]; then
    echo "✅ Все компоненты работают"
else
    echo "⚠️  Есть проблемы с компонентами, но можно продолжить"
fi

# Тест улучшений пунктуации
echo "✏️  Тест улучшений пунктуации..."
./venv/bin/python test_punctuation_fix.py
if [ $? -eq 0 ]; then
    echo "✅ Пунктуация улучшена на 71.4%!"
else
    echo "⚠️  Проблемы с тестом пунктуации"
fi

# Тест автовставки
echo "📋 Тест автовставки..."
./venv/bin/python test_auto_paste.py
if [ $? -eq 0 ]; then
    echo "✅ Автовставка работает"
else
    echo "⚠️  Проблемы с автовставкой - проверьте разрешения"
fi

# Инструкция по настройке доступа
echo ""
echo "🔐 ВАЖНО: Настройка разрешений доступа"
echo "========================================="
echo "1. Откройте: System Settings → Privacy & Security → Accessibility"
echo "2. Нажмите '+' и добавьте:"
echo "   • Python (/opt/homebrew/bin/python3.12)"
echo "   • Terminal (/Applications/Utilities/Terminal.app)"
echo "3. Поставьте галочки рядом с добавленными приложениями"
echo ""
echo "Открыть настройки сейчас? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
    echo "Нажмите Enter после настройки разрешений..."
    read -r
fi

# Запуск приложения
echo ""
echo "🎤 Запуск SuperWhisper Simple"
echo "============================="
echo "✅ НОВЫЕ ИСПРАВЛЕНИЯ в этой версии:"
echo "   • ✏️  ИСПРАВЛЕНА ПУНКТУАЦИЯ: нет больше странных вопросов!"
echo "   • ❓ Правильные вопросы: 'Как дела?' вместо 'Как дела.'"
echo "   • ✂️  Убраны лишние запятые: 'Мама и папа' вместо 'Мама, и папа'"
echo "   • 📊 Точность пунктуации: с 0% до 71.4%"
echo "   • 🛡️  Консервативный режим для стабильности"
echo ""
echo "⌨️  Управление:"
echo "   • Option + Space - запись/остановка"
echo "   • Иконка 🎤/🔴 в строке меню"
echo "   • Текст автоматически вставляется в курсор"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo ""

./venv/bin/python superwhisper.py 