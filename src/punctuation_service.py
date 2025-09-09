"""
УЛУЧШЕННЫЙ сервис для восстановления пунктуации и регистра
Исправляет проблемы с неправильными вопросительными знаками и запятыми
"""

import logging
import re
from typing import Dict, Any, List
import os

# Для BERT-модели
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None
    AutoTokenizer = None
    AutoModelForTokenClassification = None


class PunctuationService:
    """Улучшенный сервис для восстановления пунктуации и регистра в тексте"""
    
    def __init__(self, config: Any):
        """
        Инициализация улучшенного сервиса пунктуации с поддержкой BERT

        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        self.bert_pipeline = None

        # Конфигурация пунктуации
        punctuation_config = config.get("punctuation", {})
        self.mode = punctuation_config.get('mode', 'conservative')
        self.cache_dir = punctuation_config.get('cache_dir', './cache/punctuation')

        # Конфигурация модели
        model_config = punctuation_config.get('model', {})
        self.model_provider = model_config.get('provider', 'none')
        self.model_name = model_config.get('name', 'DeepPavlov/bert-base-cased-sentence')
        self.use_gpu = model_config.get('use_gpu', False)

        # Конфигурация правил
        rules_config = punctuation_config.get('rules', {})
        self.aggressive_commas = rules_config.get('aggressive_commas', False)
        self.fix_abbreviations = rules_config.get('fix_abbreviations', True)

        self.logger.info(f"Инициализация сервиса пунктуации (режим: {self.mode}, модель: {self.model_provider})")

        # Инициализация BERT-модели если возможно
        if self.model_provider != 'none':
            self._init_bert_model()

    def _init_bert_model(self):
        """
        Инициализация BERT-модели для восстановления пунктуации
        """
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers не доступны, отключаем BERT-модель")
            self.model_provider = 'none'
            return

        try:
            self.logger.info(f"Загрузка BERT-модели: {self.model_name}")

            # Создаем директорию для кэша если её нет
            os.makedirs(self.cache_dir, exist_ok=True)

            # Загружаем модель
            device = 0 if self.use_gpu and torch.cuda.is_available() else -1

            self.bert_pipeline = pipeline(
                "token-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                device=device,
                cache_dir=self.cache_dir,
                aggregation_strategy="simple"
            )

            self.logger.info("✅ BERT-модель для пунктуации загружена успешно")

        except Exception as e:
            self.logger.warning(f"⚠️ BERT-модель недоступна: {str(e).split(':')[0]}")
            self.logger.info("Переключаемся на rule-based режим (нормально)")
            self.model_provider = 'none'

    def restore_punctuation(self, text) -> str:
        """
        Восстанавливает пунктуацию и регистр в тексте
        
        Args:
            text: Исходный текст без пунктуации (строка или словарь)
            
        Returns:
            Текст с восстановленной пунктуацией и регистром
        """
        try:
            # Обрабатываем случай когда передан словарь
            if isinstance(text, dict):
                text = text.get("text", "")
            
            text = str(text)  # Приводим к строке
            
            if not text.strip():
                return text
            
            self.logger.info(f"Восстановление пунктуации для текста длиной {len(text)} символов")
            
            # ПРЕДВАРИТЕЛЬНАЯ очистка входного текста от артефактов
            text = self._pre_clean_text(text)
            
            # Выбираем метод в зависимости от режима
            if self.mode == 'bert' and self.bert_pipeline:
                # Приоритет: BERT-модель если доступна
                self.logger.info("Используем BERT-модель для восстановления пунктуации")
                return self._restore_with_bert(text)
            elif self.mode == 'conservative':
                return self._restore_conservative(text)
            elif self.mode == 'improved':
                return self._restore_improved_fixed(text)
            else:
                # Fallback на консервативный
                return self._restore_conservative(text)

        except Exception as e:
            self.logger.error(f"Ошибка восстановления пунктуации: {e}")
            # Возвращаем базовую обработку
            return self._restore_basic_safe(text)

    def _restore_with_bert(self, text: str) -> str:
        """
        Восстановление пунктуации с помощью BERT-модели

        Args:
            text: Исходный текст без пунктуации

        Returns:
            Текст с восстановленной пунктуацией
        """
        try:
            if not self.bert_pipeline:
                self.logger.warning("BERT-модель недоступна, переключаемся на rule-based")
                return self._restore_improved_fixed(text)

            self.logger.info("🔧 BERT: Анализ текста для восстановления пунктуации")

            # Получаем предсказания от модели
            predictions = self.bert_pipeline(text)

            # Применяем предсказания к тексту
            result = self._apply_bert_predictions(text, predictions)

            # Постобработка для улучшения результата
            result = self._post_process_bert_result(result)

            self.logger.info("✅ BERT: Пунктуация восстановлена")
            return result

        except Exception as e:
            self.logger.error(f"Ошибка BERT-восстановления: {e}")
            # Fallback на улучшенный rule-based
            return self._restore_improved_fixed(text)

    def _apply_bert_predictions(self, text: str, predictions: List[Dict]) -> str:
        """
        Применяет предсказания BERT-модели к тексту

        Args:
            text: Исходный текст
            predictions: Предсказания модели

        Returns:
            Текст с примененными предсказаниями
        """
        if not predictions:
            return text

        result = text
        offset = 0  # Смещение из-за вставленных символов

        for pred in predictions:
            if pred['entity'] in ['PERIOD', 'COMMA', 'QUESTION', 'EXCLAMATION']:
                # Получаем позицию для вставки
                start_pos = pred['start'] + offset

                # Определяем символ пунктуации
                if pred['entity'] == 'PERIOD':
                    punct = '.'
                elif pred['entity'] == 'COMMA':
                    punct = ','
                elif pred['entity'] == 'QUESTION':
                    punct = '?'
                elif pred['entity'] == 'EXCLAMATION':
                    punct = '!'
                else:
                    continue

                # Проверяем, что на этой позиции еще нет пунктуации
                if start_pos < len(result) and result[start_pos] not in '.!?,;:':
                    # Вставляем символ
                    result = result[:start_pos] + punct + result[start_pos:]
                    offset += 1

        return result

    def _post_process_bert_result(self, text: str) -> str:
        """
        Постобработка результата BERT-модели

        Args:
            text: Результат BERT-обработки

        Returns:
            Финально обработанный текст
        """
        # Исправляем двойные знаки препинания
        text = re.sub(r'([.!?])\1+', r'\1', text)

        # Исправляем пробелы вокруг знаков препинания
        text = re.sub(r'\s*([.!?,;:])\s*', r'\1 ', text)

        # Исправляем начало предложений (капитализация)
        sentences = re.split(r'([.!?]\s*)', text)
        result_sentences = []

        for i, sentence in enumerate(sentences):
            if i % 2 == 0:  # Текст предложения
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
            result_sentences.append(sentence)

        result = ''.join(result_sentences)

        # Финальная очистка
        result = self._post_process_safe(result)

        return result

    def _pre_clean_text(self, text: str) -> str:
        """
        ПРЕДВАРИТЕЛЬНАЯ очистка входного текста от артефактов Whisper
        Исправляет проблемы ДО основной обработки
        
        Args:
            text: Сырой текст от Whisper
            
        Returns:
            Предварительно очищенный текст
        """
        # Убираем лишние знаки препинания в начале фрагментов
        text = re.sub(r'^\s*[.,!?]+\s*', '', text)  # Убираем знаки в начале
        
        # Исправляем разорванные слова типа "В. принципе"
        text = re.sub(r'\b([А-ЯЁ])\.\s+([а-яё])', r'\1 \2', text)
        
        # Объединяем короткие фрагменты разделенные точками
        # "благодаря нашему приложению. в. принципе" → "благодаря нашему приложению в принципе"
        words = text.split()
        cleaned_words = []
        
        for i, word in enumerate(words):
            # Если это короткое слово с точкой в конце
            if len(word) <= 3 and word.endswith('.') and i < len(words) - 1:
                # И следующее слово начинается с маленькой буквы
                next_word = words[i + 1] if i + 1 < len(words) else ""
                if next_word and next_word[0].islower():
                    # Убираем точку и продолжаем
                    cleaned_words.append(word[:-1])
                    continue
            
            cleaned_words.append(word)
        
        return " ".join(cleaned_words)
    
    def _restore_conservative(self, text: str) -> str:
        """
        КОНСЕРВАТИВНОЕ восстановление пунктуации
        Минимальная обработка для максимальной надёжности
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с консервативной пунктуацией
        """
        try:
            # Очищаем текст
            result = text.strip()
            
            if not result:
                return result
            
            # Разбиваем на предложения по логическим паузам
            sentences = self._split_into_sentences_safe(result)
            
            processed_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Капитализируем первую букву
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    
                    # ИСПРАВЛЕНО: Только очевидные вопросы
                    if self._is_clear_question(sentence):
                        if not sentence.endswith('?'):
                            sentence += '?'
                    else:
                        # Обычные предложения - только точка
                        if not sentence.endswith(('.', '!', '?')):
                            sentence += '.'
                    
                    processed_sentences.append(sentence)
            
            result = " ".join(processed_sentences)
            
            # Дополнительная безопасная обработка
            result = self._post_process_safe(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка консервативной обработки: {e}")
            return self._restore_basic_safe(text)
    
    def _restore_improved_fixed(self, text: str) -> str:
        """
        ИСПРАВЛЕННОЕ улучшенное восстановление пунктуации
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с исправленной логикой пунктуации
        """
        try:
            # Очищаем текст
            result = text.strip()
            
            if not result:
                return result
            
            # Разбиваем на предложения
            sentences = self._split_into_sentences_safe(result)
            
            processed_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Капитализируем первую букву
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    
                    # ИСПРАВЛЕНО: Правильная логика вопросов
                    if self._is_clear_question(sentence):
                        if not sentence.endswith('?'):
                            sentence += '?'
                    elif self._is_exclamation(sentence):
                        if not sentence.endswith('!'):
                            sentence += '!'
                    else:
                        # Обычные предложения
                        if not sentence.endswith(('.', '!', '?')):
                            sentence += '.'
                    
                    processed_sentences.append(sentence)
            
            result = " ".join(processed_sentences)
            
            # ИСПРАВЛЕНО: Безопасная расстановка запятых
            result = self._add_commas_safe(result)
            
            # Дополнительная обработка
            result = self._post_process_safe(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка исправленной обработки: {e}")
            return self._restore_conservative(text)
    
    def _is_clear_question(self, sentence: str) -> bool:
        """
        ИСПРАВЛЕНО: Определяет является ли предложение вопросом
        
        Args:
            sentence: Предложение для анализа
            
        Returns:
            True если это явно вопрос
        """
        sentence_lower = sentence.lower().strip()
        
        # Вопросительные слова, которые НАЧИНАЮТ вопрос
        question_starters = [
            "как", "что", "кто", "где", "когда", "почему", "зачем", 
            "куда", "откуда", "какой", "какая", "какое", "какие",
            "сколько", "чей", "чья", "чьё", "чьи"
        ]
        
        # ИСПРАВЛЕНО: Проверяем только начало предложения
        for starter in question_starters:
            if sentence_lower.startswith(starter + " "):
                return True
        
        # Дополнительные паттерны вопросов
        question_patterns = [
            r"^а\s+",  # "а что", "а как"
            r"^неужели\s+",
            r"^разве\s+",
            r"^ли\s+",
            r"^может\s+ли\s+",
            r"^можно\s+ли\s+"
        ]
        
        for pattern in question_patterns:
            if re.match(pattern, sentence_lower):
                return True
        
        return False
    
    def _is_exclamation(self, sentence: str) -> bool:
        """
        Определяет является ли предложение восклицательным
        
        Args:
            sentence: Предложение для анализа
            
        Returns:
            True если это восклицание
        """
        sentence_lower = sentence.lower()
        
        exclamatory_words = [
            "стоп", "хватит", "прекрати", "остановись", "ужас", 
            "боже", "вау", "класс", "супер", "отлично", "браво"
        ]
        
        # Проверяем наличие восклицательных слов
        for word in exclamatory_words:
            if word in sentence_lower:
                return True
        
        return False
    
    def _add_commas_safe(self, text: str) -> str:
        """
        ИСПРАВЛЕНО: Безопасная расстановка запятых
        
        Args:
            text: Текст для обработки
            
        Returns:
            Текст с безопасно расставленными запятыми
        """
        # УБРАНО: агрессивные правила для союзов "и", "а", "но"
        
        # Только безопасные правила после вводных слов
        introductory_words = [
            "например", "конечно", "итак", "поэтому", "следовательно",
            "во-первых", "во-вторых", "в-третьих", "наконец", "кроме того"
        ]
        
        for word in introductory_words:
            # Добавляем запятую после вводного слова если её нет
            pattern = r'(\. |\A)(' + re.escape(word) + r') ([а-яёА-ЯЁ])'
            replacement = r'\1\2, \3'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Запятая перед "который", "которая", "которое" (относительные местоимения)
        relative_pronouns = ["который", "которая", "которое", "которые"]
        for pronoun in relative_pronouns:
            pattern = r'([а-яёА-ЯЁ]{3,}) (' + pronoun + r') '
            replacement = r'\1, \2 '
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _split_into_sentences_safe(self, text: str) -> List[str]:
        """
        УЛУЧШЕННОЕ разбиение текста на предложения
        Объединяет короткие фрагменты, избегает "В. Принципе"
        
        Args:
            text: Исходный текст
            
        Returns:
            Список предложений
        """
        # Простое разделение по ключевым словам и длине
        sentence_breaks = [
            "во-первых", "во-вторых", "в-третьих", "наконец",
            "итак", "поэтому", "однако", "тем не менее"
        ]
        
        words = text.split()
        sentences = []
        current_sentence = []
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # УЛУЧШЕНО: более умные условия разделения
            should_break = (
                len(current_sentence) > 15 or  # Увеличили лимит
                (word.lower() in sentence_breaks and len(current_sentence) > 5) or  # Минимум 5 слов
                (i < len(words) - 1 and words[i + 1].lower() in sentence_breaks and len(current_sentence) > 5)
            )
            
            # НОВОЕ: НЕ разбиваем очень короткие фрагменты (избегаем "В. Принципе")
            if should_break and len(current_sentence) > 6:  # Минимум 6 слов для разбиения
                sentences.append(" ".join(current_sentence))
                current_sentence = []
        
        # Добавляем оставшиеся слова
        if current_sentence:
            sentences.append(" ".join(current_sentence))
        
        # НОВОЕ: Объединяем слишком короткие предложения
        merged_sentences = []
        for sentence in sentences:
            # Если предложение очень короткое (1-2 слова) - объединяем с предыдущим
            if len(sentence.split()) <= 2 and merged_sentences:
                merged_sentences[-1] += " " + sentence.lower()
            else:
                merged_sentences.append(sentence)
        
        return merged_sentences
    
    def _post_process_safe(self, text: str) -> str:
        """
        БЕЗОПАСНАЯ дополнительная обработка текста
        
        Args:
            text: Текст для обработки
            
        Returns:
            Обработанный текст
        """
        # Исправляем двойные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        # МАКСИМАЛЬНО АГРЕССИВНАЯ очистка дублей (все проблемы пользователя)
        # Приоритет: ? > ! > . > ,
        text = re.sub(r'[,!.]*\?', '?', text)       # Любые знаки + ? → только ?
        text = re.sub(r'[,.]*!(?!\?)', '!', text)   # Любые знаки + ! → только ! (но не !?)
        text = re.sub(r'![.]', '!', text)           # ! + точка → только !
        text = re.sub(r'[.]+', '.', text)           # Множественные точки → одна
        text = re.sub(r'[,]+', ',', text)           # Множественные запятые → одна
        
        # Специальные случаи из примеров пользователя
        text = re.sub(r',\?', '?', text)            # ,? → ?
        text = re.sub(r'\.\?', '?', text)           # .? → ?
        text = re.sub(r'!\.$', '!', text)           # !. в конце → !
        text = re.sub(r',\.$', '.', text)           # ,. в конце → .
        
        # Очистка артефактов от пауз
        text = re.sub(r'\.\s*,', '.', text)         # Точка запятая → точка
        text = re.sub(r',\s*\.', '.', text)         # Запятая точка → точка
        
        # Убираем знаки препинания после коротких слов (В. Принципе → В принципе)
        text = re.sub(r'\b([А-ЯЁ])\.\s+([а-яё])', r'\1 \2', text)

        # Добавляем пробелы после знаков препинания
        text = re.sub(r'([.!?])([А-ЯA-Z])', r'\1 \2', text)

        # Исправляем кавычки и тире
        text = self._fix_quotes_and_dashes(text)

        # Исправляем транслитерацию технических терминов
        text = self._fix_transliteration(text)

        # ФИНАЛЬНАЯ ОЧИСТКА: убираем все лишние пробелы
        text = re.sub(r'\s+', ' ', text)  # Множественные пробелы → один пробел
        text = text.strip()               # Убираем пробелы в начале и конце

        return text
    
    def _fix_quotes_and_dashes(self, text: str) -> str:
        """
        Исправляет кавычки и тире на типографские символы

        Args:
            text: Исходный текст

        Returns:
            Текст с исправленными кавычками и тире
        """
        try:
            # Прямые кавычки на елочки
            text = re.sub(r'"([^"]*)"', r'«\1»', text)

            # Одинарные кавычки на лапки
            text = re.sub(r"'([^']*)'", r'‹\1›', text)

            # Минус на длинное тире
            text = re.sub(r'\s+-\s+', ' — ', text)

            # Три точки на многоточие
            text = re.sub(r'\.\.\.', '…', text)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка исправления кавычек и тире: {e}")
            return text

    def _fix_transliteration(self, text: str) -> str:
        """
        Исправляет транслитерацию технических терминов

        Args:
            text: Исходный текст

        Returns:
            Текст с исправленной транслитерацией
        """
        try:
            # Термины для исправления
            translit_fixes = {
                # MLX-Whisper вместо MLXWishper
                r'\bMLXWishper\b': 'MLX-Whisper',
                r'\bLarge V3\b': 'large-v3',
                r'\bгитхаб\b': 'GitHub',
                r'\bGitHub\b': 'GitHub',  # уже правильно
                r'\bприложуха\b': 'приложение',

                # Технические сокращения
                r'\bритме\b': 'README.md',
                r'\bридми\b': 'README.md',
                r'\bигнор\b': '.gitignore',
                r'\bкит игнор\b': '.gitignore',
                r'\bгид игнор\b': '.gitignore',

                # Названия
                r'\bMacBook\b': 'MacBook',
                r'\bmacOS\b': 'macOS',
                r'\bApple\b': 'Apple',

                # Общие исправления
                r'\bможешь\b': 'можешь',
                r'\bможетшь\b': 'можешь'
            }

            for pattern, replacement in translit_fixes.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка исправления транслитерации: {e}")
            return text

    def process_text(self, text: str) -> str:
        """
        Основной метод обработки текста с пунктуацией

        Args:
            text: Исходный текст

        Returns:
            Обработанный текст
        """
        if not text or not text.strip():
            return text

        try:
            # Основная обработка
            result = self.restore_punctuation(text)

            # Дополнительная постобработка
            result = self._post_process_safe(result)

            return result

        except Exception as e:
            self.logger.error(f"Ошибка обработки текста: {e}")
            return self._restore_basic_safe(text)

    def _restore_basic_safe(self, text: str) -> str:
        """
        БАЗОВАЯ безопасная обработка в случае ошибок

        Args:
            text: Исходный текст

        Returns:
            Текст с минимальной обработкой
        """
        try:
            result = text.strip()

            if not result:
                return result

            # Только капитализация первой буквы и точка в конце
            if result:
                result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()

                if not result.endswith(('.', '!', '?')):
                    result += '.'

            return result

        except Exception as e:
            self.logger.error(f"Ошибка базовой обработки: {e}")
            return text
