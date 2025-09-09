"""
Сервис кастомного словаря для SuperWhisper
Фокус на русском языке и специфике
"""

import json
import os
import logging
import re
from typing import Dict, List, Optional, Set


class VocabularyService:
    """Сервис для работы с кастомным словарем"""

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Пути к файлам словаря
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.vocab_dir = os.path.join(self.base_dir, "vocabulary")

        # Настройки
        self.enabled = True
        self.expand_abbreviations = True
        self.capitalize_names = True
        self.handle_compound_words = True

        if config and hasattr(config, 'vocabulary'):
            vocab_config = config.vocabulary
            self.enabled = vocab_config.get('enabled', True)
            self.expand_abbreviations = vocab_config.get('expand_abbreviations', True)
            self.capitalize_names = vocab_config.get('capitalize_names', True)
            self.handle_compound_words = vocab_config.get('handle_compound_words', True)

        # Загружаем словари
        self.custom_terms = self._load_vocabulary("custom_terms.json")
        self.abbreviations = self._load_vocabulary("abbreviations.json")
        self.names = self._load_vocabulary("names.json")

        # Кэш для производительности
        self._compiled_patterns = {}

        self.logger.info(f"📚 VocabularyService инициализирован: {len(self.custom_terms)} терминов, "
                        f"{len(self.abbreviations)} сокращений, {len(self.names)} имен")

    def _load_vocabulary(self, filename: str) -> Dict:
        """Загружает словарь из JSON файла"""
        try:
            filepath = os.path.join(self.vocab_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.debug(f"Загружен словарь: {filename} ({len(data)} записей)")
                    return data
            else:
                self.logger.warning(f"Файл словаря не найден: {filepath}")
                return {}
        except Exception as e:
            self.logger.error(f"Ошибка загрузки словаря {filename}: {e}")
            return {}

    def process_text(self, text: str) -> str:
        """Обрабатывает текст с использованием словаря"""
        if not self.enabled:
            return text

        try:
            # Применяем все обработки
            if self.expand_abbreviations:
                text = self._expand_abbreviations(text)

            if self.capitalize_names:
                text = self._capitalize_names(text)

            if self.handle_compound_words:
                text = self._handle_compound_words(text)

            # Обработка специфики русского языка
            text = self._apply_russian_rules(text)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка обработки текста словарем: {e}")
            return text

    def _expand_abbreviations(self, text: str) -> str:
        """Расширяет аббревиатуры в тексте"""
        try:
            # Сортируем аббревиатуры по длине (сначала длинные, потом короткие)
            # Это важно для обработки составных терминов
            sorted_abbrs = sorted(self.abbreviations.items(),
                                key=lambda x: len(x[0]), reverse=True)

            for abbr, data in sorted_abbrs:
                if isinstance(data, dict) and 'expand' in data:
                    expand_to = data.get('context', data['expand'])  # Предпочитаем русский контекст

                    # Специальная обработка для составных терминов
                    if ' ' in abbr:  # Составной термин (например, "MLX Whisper")
                        # Ищем точное совпадение фразы
                        pattern = r'\b' + re.escape(abbr) + r'\b'
                        text = re.sub(pattern, expand_to, text, flags=re.IGNORECASE)
                    else:
                        # Обычная аббревиатура
                        pattern = r'\b' + re.escape(abbr) + r'\b'
                        text = re.sub(pattern, expand_to, text, flags=re.IGNORECASE)

            # Дополнительная обработка специфичных случаев Whisper
            text = self._fix_whisper_artifacts(text)

            return text
        except Exception as e:
            self.logger.error(f"Ошибка расширения аббревиатур: {e}")
            return text

    def _fix_whisper_artifacts(self, text: str) -> str:
        """Исправляет специфичные артефакты Whisper модели"""
        try:
            # Исправляем "Apple MLX framework. OpenAI Whisper model" → "MLX Whisper"
            text = re.sub(r'Apple\s+MLX\s+framework\.?\s*OpenAI\s+Whisper\s+model',
                         'MLX Whisper', text, flags=re.IGNORECASE)

            # Более агрессивный вариант - исправляем любую комбинацию
            text = re.sub(r'Apple\s+MLX\s+framework(?:\.?\s*OpenAI\s+Whisper\s+model)?',
                         'MLX Whisper', text, flags=re.IGNORECASE)

            # Исправляем "Apple MLX framework" → "MLX"
            text = re.sub(r'Apple\s+MLX\s+framework', 'MLX', text, flags=re.IGNORECASE)

            # Исправляем "OpenAI Whisper model" → "Whisper"
            text = re.sub(r'OpenAI\s+Whisper\s+model', 'Whisper', text, flags=re.IGNORECASE)

            # Исправляем "операционная система" → "macOS" в контексте
            text = re.sub(r'для\s+Mac\s+операционная\s+система',
                         'для macOS', text, flags=re.IGNORECASE)

            # Исправляем "Voice – to – Text" → "Voice-to-Text"
            text = re.sub(r'\bVoice\s*–\s*to\s*–\s*Text\b', 'Voice-to-Text', text, flags=re.IGNORECASE)

            # Исправляем "Voice to Text" → "Voice-to-Text"
            text = re.sub(r'\bVoice\s+to\s+Text\b', 'Voice-to-Text', text, flags=re.IGNORECASE)

            # Исправляем "Voice To Text" → "Voice-to-Text"
            text = re.sub(r'\bVoice\s+To\s+Text\b', 'Voice-to-Text', text, flags=re.IGNORECASE)

            # Исправляем "post-обработку" → "постобработку"
            text = re.sub(r'post\s*-\s*обработку', 'постобработку', text, flags=re.IGNORECASE)

            # Исправляем "слов-паразитов" → "слов-паразитов"
            text = re.sub(r'слов\s*-\s*паразитов', 'слов-паразитов', text, flags=re.IGNORECASE)

            return text
        except Exception as e:
            self.logger.error(f"Ошибка исправления артефактов Whisper: {e}")
            return text

    def _capitalize_names(self, text: str) -> str:
        """Правильно капитализирует имена, фамилии и специальные слова"""
        try:
            if not self.names:
                return text

            words = text.split()

            for i, word in enumerate(words):
                word_lower = word.lower()

                # Проверяем имена
                if 'имена' in self.names and word_lower in self.names['имена']:
                    words[i] = word.capitalize()

                # Проверяем фамилии
                elif 'фамилии' in self.names and word_lower in self.names['фамилии']:
                    words[i] = word.capitalize()

                # Проверяем отчества
                elif 'отчества' in self.names and word_lower in self.names['отчества']:
                    words[i] = word_lower.capitalize()

                # Проверяем специальные слова
                elif 'специальные_слова' in self.names and word_lower in self.names['специальные_слова']:
                    words[i] = word.capitalize()

            return ' '.join(words)

        except Exception as e:
            self.logger.error(f"Ошибка капитализации имен: {e}")
            return text

    def _handle_compound_words(self, text: str) -> str:
        """Обрабатывает сложные слова"""
        try:
            # Исправляем распространенные проблемы с сложными словами
            replacements = {
                r'\bв принципе\b': 'в принципе',
                r'\bт е\b': 'т.е.',
                r'\bи т д\b': 'и т.д.',
                r'\bи т п\b': 'и т.п.',
                r'\bт к\b': 'т.к.',
                r'\bв т ч\b': 'в т.ч.',
                r'\bд р\b': 'др.',
                r'\bг\b': 'г.',  # город
                r'\bул\b': 'ул.',  # улица
            }

            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка обработки сложных слов: {e}")
            return text

    def _apply_russian_rules(self, text: str) -> str:
        """Применяет специфические правила русского языка"""
        try:
            # Убираем неправильную замену всех 'е' на 'ё' - это ломает текст!
            # Вместо этого добавляем более умную обработку только для слов где это нужно

            # Исправляем только очевидные случаи, где Whisper путает ё/е
            corrections = {
                'делае': 'делает',
                'делаЕ': 'Делает',
                'сделае': 'сделает',
                'сделаЕ': 'Сделает',
                'скаже': 'скажет',
                'скажЕ': 'Скажет',
                'покаже': 'покажет',
                'покажЕ': 'Покажет',
                'буде': 'будет',
                'будЕ': 'Будет',
                'може': 'может',
                'можЕ': 'Может',
                'умее': 'умеет',
                'умеЕ': 'Умеет',
                'знае': 'знает',
                'знаЕ': 'Знает',
                # Исправления для названия проекта ScanovichAI
                'сканович аа': 'ScanovichAI',
                'сканович': 'ScanovichAI',
                'Сканович АА': 'ScanovichAI',
                'Сканович': 'ScanovichAI',
                'scanovich искусственный интеллект': 'ScanovichAI',
                'Scanovich искусственный интеллект': 'ScanovichAI',
                'scanovich ai': 'ScanovichAI',
                'Scanovich ai': 'ScanovichAI',
                'scanovichai': 'ScanovichAI',
                'Scanovichai': 'ScanovichAI',
            }

            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)

            # Исправляем заглавные буквы после двоеточия
            text = re.sub(r':\s*([а-я])', lambda m: ': ' + m.group(1).upper(), text)

            # Исправляем предлоги в начале предложения
            text = re.sub(r'(^|[.!?]\s+)(в|на|с|по|из|к|от|у)\s',
                         lambda m: m.group(1) + m.group(2).lower() + ' ', text)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка применения русских правил: {e}")
            return text

    def add_custom_term(self, term: str, variations: List[str] = None, context: str = ""):
        """Добавляет новый термин в словарь"""
        try:
            if variations is None:
                variations = [term]

            self.custom_terms[term] = {
                "variations": variations,
                "expand": term,
                "context": context
            }

            self._save_vocabulary("custom_terms.json", self.custom_terms)
            self.logger.info(f"Добавлен новый термин: {term}")

        except Exception as e:
            self.logger.error(f"Ошибка добавления термина: {e}")

    def add_abbreviation(self, abbr: str, expansion: str, context: str = ""):
        """Добавляет новую аббревиатуру"""
        try:
            self.abbreviations[abbr] = {
                "expand": expansion,
                "context": context
            }

            self._save_vocabulary("abbreviations.json", self.abbreviations)
            self.logger.info(f"Добавлена аббревиатура: {abbr} -> {expansion}")

        except Exception as e:
            self.logger.error(f"Ошибка добавления аббревиатуры: {e}")

    def _save_vocabulary(self, filename: str, data: Dict):
        """Сохраняет словарь в файл"""
        try:
            filepath = os.path.join(self.vocab_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения словаря {filename}: {e}")

    def get_stats(self) -> Dict:
        """Возвращает статистику словаря"""
        return {
            "custom_terms": len(self.custom_terms),
            "abbreviations": len(self.abbreviations),
            "names": len(self.names) if self.names else 0,
            "enabled": self.enabled
        }
