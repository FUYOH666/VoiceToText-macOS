"""
Сервис для восстановления пунктуации и регистра
"""

import logging
import re
from typing import Dict, Any, List
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification


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
        # Загрузка модели может быть тяжёлой; загружаем лениво при первом использовании
        # чтобы не держать память без необходимости
        try:
            lazy_key = "lazy_load"
            lazy = getattr(self.config, "models", {}).get("punctuation", {}).get(lazy_key, True)
        except Exception:
            lazy = True

        if not lazy:
            self._load_model()
    
    def _load_model(self):
        """Загружает модель для восстановления пунктуации"""
        try:
            model_name = self.config.models["punctuation"]["model_name"]
            cache_dir = Path(self.config.models["punctuation"]["cache_dir"])
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Загрузка модели пунктуации: {model_name}")
            
            # Загружаем токенизатор и модель
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(cache_dir)
            )
            
            model = AutoModelForTokenClassification.from_pretrained(
                model_name,
                cache_dir=str(cache_dir)
            )
            
            # Создаем pipeline для NER
            self.model = pipeline(
                "ner",
                model=model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=-1  # CPU
            )
            
            self.logger.info("Модель пунктуации успешно загружена")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели пунктуации: {e}")
            # Используем fallback метод
            self.model = None
            self.logger.warning("Будет использован базовый метод пунктуации")
    
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
            
            # Если модель ещё не загружена — загружаем по требованию
            if self.model is None:
                try:
                    self._load_model()
                except Exception:
                    # Падаем обратно на базовую логику
                    self.model = None

            # Если модель теперь доступна — используем её
            if self.model is not None:
                return self._restore_with_model(text)
            else:
                return self._restore_basic(text)
                
        except Exception as e:
            self.logger.error(f"Ошибка восстановления пунктуации: {e}")
            # Возвращаем базовую обработку
            return self._restore_basic(text)
    
    def _restore_with_model(self, text: str) -> str:
        """
        Восстанавливает пунктуацию с помощью ML модели
        
        Args:
            text: Исходный текст
            
        Returns:
            Обработанный текст
        """
        try:
            # Разбиваем длинный текст на части
            max_length = 400  # Максимальная длина для модели
            
            if len(text) <= max_length:
                return self._process_chunk(text)
            
            # Обрабатываем по частям
            chunks = self._split_text(text, max_length)
            processed_chunks = []
            
            for chunk in chunks:
                processed_chunk = self._process_chunk(chunk)
                processed_chunks.append(processed_chunk)
            
            return " ".join(processed_chunks)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки с моделью: {e}")
            return self._restore_basic(text)
    
    def _process_chunk(self, text: str) -> str:
        """
        Обрабатывает один фрагмент текста
        
        Args:
            text: Фрагмент текста
            
        Returns:
            Обработанный фрагмент
        """
        try:
            # Получаем предсказания модели
            predictions = self.model(text)
            
            # Простая эвристика для восстановления пунктуации
            # (В идеале здесь должна быть более сложная логика)
            result = text
            
            # Капитализируем первое слово
            words = result.split()
            if words:
                words[0] = words[0].capitalize()
                result = " ".join(words)
            
            # Добавляем точку в конце если её нет
            if not result.endswith(('.', '!', '?')):
                result += '.'
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки фрагмента: {e}")
            return self._restore_basic(text)
    
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
        
        # Исправляем пробелы перед знаками препинания
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        # Добавляем пробелы после знаков препинания
        text = re.sub(r'([.!?])([А-ЯA-Z])', r'\1 \2', text)
        
        return text.strip() 