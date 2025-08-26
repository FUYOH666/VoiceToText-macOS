"""
Сервис для восстановления пунктуации и регистра
"""

import logging
import re
from typing import Dict, Any, List
from pathlib import Path


class PunctuationService:
    """Сервис для восстановления пунктуации и регистра в тексте"""
    
    def __init__(self, config: Any):
        """
        Инициализация сервиса пунктуации
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        # По умолчанию используем улучшенный метод без ML модели
        self.logger.info("Инициализация сервиса пунктуации без ML модели")
    
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
            
            self.logger.info(f"Восстановление пунктуации для текста длиной "
                           f"{len(text)} символов")
            
            # Используем улучшенный метод пунктуации без ML модели
            return self._restore_improved(text)
                
        except Exception as e:
            self.logger.error(f"Ошибка восстановления пунктуации: {e}")
            # Возвращаем базовую обработку
            return self._restore_basic(text)
    
    def _restore_improved(self, text: str) -> str:
        """
        Улучшенное восстановление пунктуации без ML модели
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с улучшенной пунктуацией
        """
        try:
            # Очищаем текст
            result = text.strip()
            
            if not result:
                return result
            
            # Разбиваем на предложения по логическим паузам и словам
            sentences = self._split_into_sentences(result)
            
            processed_sentences = []
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if sentence:
                    # Капитализируем первую букву
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    
                    # Определяем тип предложения по ключевым словам
                    question_words = ["как", "почему", "когда", "где", "что", "зачем", "кто", "куда", "откуда"]
                    exclamatory_words = ["стоп", "хватит", "прекрати", "остановись", "ужас", "боже", "вау"]
                    
                    if any(word in sentence.lower() for word in question_words) and not any(sentence.lower().startswith(q) for q in question_words):
                        # Вопросительные предложения (кроме начинающихся с вопросительных слов)
                        if not sentence.endswith('?'):
                            sentence += '?'
                    elif any(word in sentence.lower() for word in exclamatory_words):
                        # Восклицательные предложения
                        if not sentence.endswith('!'):
                            sentence += '!'
                    else:
                        # Обычные предложения
                        if not sentence.endswith(('.', '!', '?')):
                            sentence += '.'
                    
                    processed_sentences.append(sentence)
            
            result = " ".join(processed_sentences)
            
            # Добавляем запятые в типичных местах
            result = self._add_commas(result)
            
            # Дополнительная обработка
            result = self._post_process(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка улучшенной обработки: {e}")
            return self._restore_basic(text)
    
    def _add_commas(self, text: str) -> str:
        """
        Добавляет запятые в текст
        
        Args:
            text: Текст для обработки
            
        Returns:
            Текст с запятыми
        """
        # Простые правила для добавления запятых
        # Перед союзами "и", "а", "но", "однако"
        text = re.sub(r'(\w+) (и|а|но|однако) (\w+)', r'\1, \2 \3', text, flags=re.IGNORECASE)
        
        # После вводных слов
        introductory_words = ["например", "конечно", "однако", "итак", "поэтому", "следовательно", "во-первых", "во-вторых"]
        for word in introductory_words:
            pattern = r'(\. |\A)(' + word + r') (\w+)'
            replacement = r'\1\2, \3'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Перед "что", "как", "который" если это подчинительные союзы
        subordinating_conjunctions = ["что", "как", "который", "когда", "поскольку", "так как"]
        for conj in subordinating_conjunctions:
            pattern = r'(\w{4,}) (' + conj + r') (\w+)'
            replacement = r'\1, \2 \3'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _restore_basic(self, text: str) -> str:
        """
        Базовое восстановление пунктуации без ML модели
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с базовой пунктуацией
        """
        try:
            # Очищаем текст
            result = text.strip()
            
            if not result:
                return result
            
            # Разбиваем на предложения по логическим паузам
            sentences = self._split_into_sentences(result)
            
            processed_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Капитализируем первую букву
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    
                    # Добавляем точку если её нет
                    if not sentence.endswith(('.', '!', '?', ',')):
                        sentence += '.'
                    
                    processed_sentences.append(sentence)
            
            result = " ".join(processed_sentences)
            
            # Дополнительная обработка
            result = self._post_process(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка базовой обработки: {e}")
            return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Разбивает текст на предложения
        
        Args:
            text: Исходный текст
            
        Returns:
            Список предложений
        """
        # Ключевые слова для разделения предложений
        sentence_breaks = [
            "и так", "итак", "поэтому", "однако", "тем не менее",
            "во-первых", "во-вторых", "в-третьих", "наконец",
            "кроме того", "более того", "также"
        ]
        
        # Простое разделение по длине и ключевым словам
        words = text.split()
        sentences = []
        current_sentence = []
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # Проверяем условия для разделения
            should_break = (
                len(current_sentence) > 15 or  # Длинное предложение
                word.lower() in sentence_breaks or  # Ключевое слово
                (i < len(words) - 1 and words[i + 1].lower() in sentence_breaks)
            )
            
            if should_break and len(current_sentence) > 3:
                sentences.append(" ".join(current_sentence))
                current_sentence = []
        
        # Добавляем оставшиеся слова
        if current_sentence:
            sentences.append(" ".join(current_sentence))
        
        return sentences
    
    def _split_text(self, text: str, max_length: int) -> List[str]:
        """
        Разбивает текст на фрагменты заданной длины
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина фрагмента
            
        Returns:
            Список фрагментов
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 для пробела
            
            if current_length + word_length > max_length and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _post_process(self, text: str) -> str:
        """
        Дополнительная обработка текста
        
        Args:
            text: Текст для обработки
            
        Returns:
            Обработанный текст
        """
        # Исправляем двойные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Исправляем пробелы перед знаками препинания, но сохраняем правильные знаки
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        # Добавляем пробелы после знаков препинания, если за ними следует заглавная буква
        text = re.sub(r'([.!?])([А-ЯA-Z])', r'\1 \2', text)
        
        # Исправляем случаи с лишними знаками препинания перед вопросительными знаками
        text = re.sub(r'([.!?])\s*\?', r'?', text)
        
        # Исправляем случаи с лишними знаками препинания перед восклицательными знаками
        text = re.sub(r'([.!?])\s*!', r'!', text)
        
        return text.strip()