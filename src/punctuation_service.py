"""
УЛУЧШЕННЫЙ сервис для восстановления пунктуации и регистра
Исправляет проблемы с неправильными вопросительными знаками и запятыми
"""

import logging
import re
from typing import Dict, Any, List
from pathlib import Path


class PunctuationService:
    """Улучшенный сервис для восстановления пунктуации и регистра в тексте"""
    
    def __init__(self, config: Any):
        """
        Инициализация улучшенного сервиса пунктуации
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        
        # Режимы работы
        punctuation_config = config.models.get("punctuation", {})
        self.mode = punctuation_config.get('mode', 'conservative')
        self.logger.info(f"Инициализация улучшенного сервиса пунктуации (режим: {self.mode})")
    
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
            if self.mode == 'conservative':
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
        
        # ФИНАЛЬНАЯ ОЧИСТКА: убираем все лишние пробелы
        text = re.sub(r'\s+', ' ', text)  # Множественные пробелы → один пробел
        text = text.strip()               # Убираем пробелы в начале и конце
        
        return text
    
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
