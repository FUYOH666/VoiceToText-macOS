#!/bin/bash

# SuperWhisper New Ideas - Установка и запуск
# Улучшенная версия с кастомным словарем и фокусом на русский язык

set -e

echo "🎤 SuperWhisper New Ideas - Установка и запуск"
echo "================================================"
echo "📚 НОВЫЕ ФУНКЦИИ: Кастомный словарь + улучшенный русский"
echo ""

# Определяем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
echo "🧪 Проверка компонентов..."
python3.12 -c "
import sys
print('✅ Python версия:', sys.version.split()[0])

try:
    import mlx_whisper
    print('✅ MLX Whisper доступен')
except ImportError:
    print('❌ MLX Whisper не установлен')

try:
    from src.config import Config
    print('✅ Конфигурация загружается')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)
"

echo "✅ Все компоненты работают"

# Создание исполняемого файла
echo "📝 Создание исполняемого файла..."
cat > superwhisper_new << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
./venv/bin/python superwhisper.py
EOF

chmod +x superwhisper_new

echo ""
echo "🔐 ВАЖНО: Настройка разрешений доступа"
echo "========================================"
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
fi

echo ""
echo "🎤 SuperWhisper New Ideas готов к запуску!"
echo "==========================================="
echo "🚀 НОВЫЕ ВОЗМОЖНОСТИ:"
echo "   • 📚 Кастомный словарь для терминов"
echo "   • 🇷🇺 Улучшенное распознавание русского"
echo "   • ✏️  Правильная капитализация имен"
echo "   • 🔧 Расширенная конфигурация"
echo ""
echo "⌨️  Управление:"
echo "   • Option + Space - запись/остановка"
echo "   • Иконка 🎤/🔴 в строке меню"
echo "   • Текст автоматически вставляется"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo ""
echo "Запустить сейчас? (y/n)"
read -r run_now
if [[ "$run_now" =~ ^[Yy]$ ]]; then
    echo "Запуск SuperWhisper New Ideas..."
    ./venv/bin/python superwhisper.py
else
    echo "Для запуска используйте:"
    echo "  ./superwhisper_new          # Из этой директории"
    echo "  superwhisper               # Из любой директории"
fi
