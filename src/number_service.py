"""
Сервис форматирования чисел для SuperWhisper
Преобразует числа в читаемый формат: пробелы, проценты, диапазоны
"""

import logging
import re
from typing import Dict, List, Optional


class NumberService:
    """Сервис для форматирования чисел и единиц измерения"""

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Настройки
        self.enabled = True
        self.format_numbers = True
        self.format_percentages = True
        self.format_ranges = True
        self.format_units = True
        self.quiet_mode = True  # Тихий режим без логов

        if config and hasattr(config, 'numbers'):
            numbers_config = config.numbers
            self.enabled = numbers_config.get('enabled', True)
            self.format_numbers = numbers_config.get('format_numbers', True)
            self.format_percentages = numbers_config.get('format_percentages', True)
            self.format_ranges = numbers_config.get('format_ranges', True)
            self.format_units = numbers_config.get('format_units', True)

        # Паттерны для чисел
        self.number_patterns = {
            # Основные числа (3 500, 5 000)
            'large_number': re.compile(r'\b(\d{1,3})(?=(\d{3})+(?!\d))'),

            # Проценты (5% -> 5 %, 10 процентов -> 10%)
            'percentage': re.compile(r'\b(\d+)(?:\s*)%(?:\s*(?:процент(?:а|ов)?|percent)?)?\b', re.IGNORECASE),

            # Диапазоны (5-10 -> 5–10, от 5 до 10 -> 5–10)
            'range_dash': re.compile(r'\b(\d+)\s*-\s*(\d+)\b'),
            'range_from_to': re.compile(r'\bот\s+(\d+)\s+до\s+(\d+)\b', re.IGNORECASE),

            # Единицы измерения
            'units': re.compile(r'\b(\d+)\s*(звонков|рубл(?:ей|я|ь)|долларов|евро|процент(?:а|ов)?|штук|часов|минут|секунд|дней|недель|месяцев|лет|километров|метров|граммов|килограммов|тонн)\b', re.IGNORECASE)
        }

        # Сокращения единиц
        self.unit_abbreviations = {
            'звонков': 'звонков',
            'рублей': 'руб.',
            'рубля': 'руб.',
            'рубль': 'руб.',
            'долларов': 'USD',
            'евро': 'EUR',
            'процентов': 'процент.',
            'процента': 'процент.',
            'штук': 'шт.',
            'часов': 'ч.',
            'минут': 'мин.',
            'секунд': 'сек.',
            'дней': 'дн.',
            'недель': 'нед.',
            'месяцев': 'мес.',
            'лет': 'л.',
            'километров': 'км.',
            'метров': 'м.',
            'граммов': 'г.',
            'килограммов': 'кг.',
            'тонн': 'т.'
        }

        self.logger.info("🔢 NumberService инициализирован")

    def process_text(self, text: str) -> str:
        """Обрабатывает текст, форматируя числа"""
        if not self.enabled or not text:
            return text

        try:
            # Шаг 1: Форматирование больших чисел (пробелы)
            if self.format_numbers:
                text = self._format_large_numbers(text)

            # Шаг 2: Форматирование процентов
            if self.format_percentages:
                text = self._format_percentages(text)

            # Шаг 3: Форматирование диапазонов
            if self.format_ranges:
                text = self._format_ranges(text)

            # Шаг 4: Форматирование единиц измерения
            if self.format_units:
                text = self._format_units(text)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка форматирования чисел: {e}")
            return text

    def _format_large_numbers(self, text: str) -> str:
        """Форматирует большие числа с тонкими пробелами (3500 -> 3 500)"""
        try:
            def add_spaces(match):
                number = match.group(0)
                # Используем тонкий неразрывный пробел (U+202F)
                thin_space = '\u202F'
                return re.sub(r'(\d)(?=(\d{3})+(?!\d))', r'\1' + thin_space, number)

            return self.number_patterns['large_number'].sub(add_spaces, text)

        except Exception as e:
            self.logger.error(f"Ошибка форматирования больших чисел: {e}")
            return text

    def _format_percentages(self, text: str) -> str:
        """Форматирует проценты (5% -> 5 %, 10 процентов -> 10%)"""
        try:
            def format_percentage(match):
                number = match.group(1)
                return f"{number}%"

            return self.number_patterns['percentage'].sub(format_percentage, text)

        except Exception as e:
            self.logger.error(f"Ошибка форматирования процентов: {e}")
            return text

    def _format_ranges(self, text: str) -> str:
        """Форматирует диапазоны (5-10 -> 5–10, от 5 до 10 -> 5–10)"""
        try:
            # Сначала обрабатываем "от X до Y"
            def format_from_to(match):
                start = match.group(1)
                end = match.group(2)
                return f"{start}–{end}"

            text = self.number_patterns['range_from_to'].sub(format_from_to, text)

            # Затем обрабатываем X-Y
            def format_dash_range(match):
                start = match.group(1)
                end = match.group(2)
                return f"{start}–{end}"

            text = self.number_patterns['range_dash'].sub(format_dash_range, text)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка форматирования диапазонов: {e}")
            return text

    def _format_units(self, text: str) -> str:
        """Форматирует единицы измерения с сокращениями"""
        try:
            def format_unit(match):
                number = match.group(1)
                unit = match.group(2).lower()

                # Ищем сокращение для единицы
                abbreviated_unit = self.unit_abbreviations.get(unit, unit)

                return f"{number} {abbreviated_unit}"

            return self.number_patterns['units'].sub(format_unit, text)

        except Exception as e:
            self.logger.error(f"Ошибка форматирования единиц: {e}")
            return text

    def add_custom_unit(self, full_name: str, abbreviation: str):
        """Добавляет пользовательскую единицу измерения"""
        try:
            self.unit_abbreviations[full_name.lower()] = abbreviation
            self.logger.info(f"Добавлена единица: {full_name} -> {abbreviation}")
        except Exception as e:
            self.logger.error(f"Ошибка добавления единицы: {e}")

    def format_specific_number(self, number: str) -> str:
        """Форматирует конкретное число"""
        try:
            # Создаем временный текст с числом
            temp_text = f" {number} "
            formatted_text = self.process_text(temp_text)
            # Извлекаем отформатированное число
            return formatted_text.strip()
        except Exception as e:
            self.logger.error(f"Ошибка форматирования числа {number}: {e}")
            return number

    def get_stats(self) -> Dict:
        """Возвращает статистику сервиса"""
        return {
            "enabled": self.enabled,
            "format_numbers": self.format_numbers,
            "format_percentages": self.format_percentages,
            "format_ranges": self.format_ranges,
            "format_units": self.format_units,
            "unit_abbreviations_count": len(self.unit_abbreviations)
        }

    @staticmethod
    def is_number_like(text: str) -> bool:
        """Проверяет, содержит ли текст числоподобные конструкции"""
        number_indicators = [
            re.compile(r'\d{4,}'),  # Большие числа
            re.compile(r'\d+%'),    # Проценты
            re.compile(r'\d+-\d+'), # Диапазоны
            re.compile(r'от \d+ до \d+', re.IGNORECASE)  # Диапазоны словами
        ]

        return any(pattern.search(text) for pattern in number_indicators)
