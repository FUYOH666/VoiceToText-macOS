"""
Сервис для распознавания речи через MLX Whisper
"""
# pylint: disable=line-too-long

import logging
import numpy as np
import gc
from pathlib import Path
from typing import Dict, Any
import mlx_whisper
from .memory_manager import free_memory


class WhisperService:
    """Сервис для распознавания речи с использованием MLX Whisper"""
    
    def __init__(self, config: Any):
        """
        Инициализация сервиса Whisper
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 🆕 Настройки управления памятью
        performance = config.performance
        gc_key = "force_garbage_collection"
        self.force_gc = performance.get(gc_key, True)
        cache_key = "clear_model_cache_after_use"
        self.clear_cache = performance.get(cache_key, True)
        
        self.logger.info("MLX Whisper сервис инициализирован")
        
        # Предварительно вычисляем предпочтительный путь к модели
        self._preferred_model_path = self._resolve_whisper_path()
    
    def transcribe(
        self, 
        audio_data: np.ndarray, 
        language: str = "ru"
    ) -> Dict[str, Any]:
        """
        Распознает речь из аудио данных
        
        Args:
            audio_data: Аудио данные в виде numpy array
            language: Язык распознавания (по умолчанию русский)
            
        Returns:
            Словарь с результатами распознавания
        """
        try:
            duration = len(audio_data) / 16000
            msg = f"Начало распознавания речи, длина: {duration:.2f}с"
            self.logger.info(msg)
            
            # 🆕 Очистка памяти перед транскрипцией
            if self.force_gc:
                gc.collect()
            
            # Транскрибируем аудио с защитой от повторений
            whisper_path = self._preferred_model_path

            result = mlx_whisper.transcribe(
                audio=audio_data,
                path_or_hf_repo=whisper_path,
                temperature=0.2,  # 🛠 Увеличиваем для разнообразия
                compression_ratio_threshold=2.0,  # 🛠 Строже против повторений
                logprob_threshold=-0.8,  # 🛠 Более строгий порог
                no_speech_threshold=0.6,
                condition_on_previous_text=False,  # 🛠 ОТКЛЮЧАЕМ для избежания циклов
                suppress_tokens=[-1],  # 🛠 Подавляем проблемные токены
                word_timestamps=True,
                language=language
            )
            
            # Форматируем результат с очисткой от повторений
            segments = result.get("segments", [])
            clean_text = self._remove_repetitions(result["text"].strip())
            formatted_result = {
                "text": clean_text,
                "language": result.get("language", language),
                "segments": segments,
                "words": self._extract_words(segments),
                "duration": len(audio_data) / 16000,
                "confidence": self._calculate_confidence(segments)
            }
            
            # 🆕 Очистка памяти после транскрипции
            if self.clear_cache:
                self._cleanup_memory()
                free_memory("whisper-after-transcribe")
            
            text_preview = formatted_result['text'][:100]
            final_msg = f"Распознавание завершено. Текст: {text_preview}..."
            self.logger.info(final_msg)
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Ошибка распознавания речи: {e}")
            # 🆕 Очистка памяти даже при ошибке
            if self.clear_cache:
                self._cleanup_memory()
                free_memory("whisper-after-file")
            raise
    
    def transcribe_file(
        self, 
        audio_file: str, 
        language: str = "ru"
    ) -> Dict[str, Any]:
        """
        Распознает речь из аудио файла
        
        Args:
            audio_file: Путь к аудио файлу
            language: Язык распознавания
            
        Returns:
            Словарь с результатами распознавания
        """
        try:
            file_path = Path(audio_file)
            if not file_path.exists():
                err_msg = f"Аудио файл не найден: {audio_file}"
                raise FileNotFoundError(err_msg)
            
            self.logger.info(f"Распознавание файла: {audio_file}")
            
            # 🆕 Очистка памяти перед транскрипцией
            if self.force_gc:
                gc.collect()
            
            # Используем MLX Whisper для файла с защитой от повторений
            whisper_path = self._preferred_model_path

            result = mlx_whisper.transcribe(
                audio=str(file_path),
                path_or_hf_repo=whisper_path,
                temperature=0.2,
                compression_ratio_threshold=2.0,
                logprob_threshold=-0.8,
                no_speech_threshold=0.6,
                condition_on_previous_text=False,
                suppress_tokens=[-1],
                language=language,
                word_timestamps=True
            )
            
            segments = result.get("segments", [])
            clean_text = self._remove_repetitions(result["text"].strip())
            formatted_result = {
                "text": clean_text,
                "language": result.get("language", language),
                "segments": segments,
                "words": self._extract_words(segments),
                "confidence": self._calculate_confidence(segments)
            }
            
            # 🆕 Очистка памяти после транскрипции
            if self.clear_cache:
                self._cleanup_memory()
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Ошибка распознавания файла: {e}")
            # 🆕 Очистка памяти даже при ошибке
            if self.clear_cache:
                self._cleanup_memory()
            raise
    
    def _cleanup_memory(self):
        """🆕 Принудительная очистка памяти после работы с моделью"""
        try:
            # Принудительная сборка мусора
            if self.force_gc:
                gc.collect()
            
            self.logger.debug("Память после Whisper очищена")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки памяти Whisper: {e}")

    def _resolve_whisper_path(self) -> str:
        """Определяет путь к локальной модели. Ошибку бросает, если модель не найдена."""
        try:
            cfg = self.config.models.get("whisper", {})
            cfg_path = cfg.get("path")
            if cfg_path:
                p = Path(str(cfg_path))
                if p.exists():
                    return str(p)
            # Популярный локальный путь по умолчанию
            default_local = Path("models/whisper-large-v3-mlx")
            if default_local.exists():
                return str(default_local)
            # Корневой каталог моделей (если внутри уже лежат config.json/weights.npz)
            root_models = Path("models")
            if root_models.exists():
                cfg_file = root_models / "config.json"
                weights_file = root_models / "weights.npz"
                if cfg_file.exists() and weights_file.exists():
                    return str(root_models)
            # Ничего не нашли — сообщаем понятной ошибкой
            raise FileNotFoundError(
                "Не найдена локальная модель Whisper. Скачайте файлы модели (config.json, "
                "weights.npz) со страницы `mlx-community/whisper-large-v3-mlx` и поместите их "
                "в каталог ./models, либо укажите корректный путь в config.yaml (models.whisper.path)."
            )
        except Exception:
            raise

    def _local_model_dir(self) -> str | None:
        """Возвращает путь к локальной модели, если она существует."""
        # 1) Конфиг-значение, если это каталог
        try:
            cfg = self.config.models.get("whisper", {})
            cfg_path = cfg.get("path")
            if cfg_path and Path(str(cfg_path)).exists():
                return str(Path(str(cfg_path)))
        except Exception:
            pass
        # 2) Дефолтный каталог
        candidate = Path("models/whisper-large-v3-mlx")
        if candidate.exists():
            return str(candidate)
        # 3) Корень models с файлами модели
        root_models = Path("models")
        cfg_file = root_models / "config.json"
        weights_file = root_models / "weights.npz"
        if root_models.exists() and cfg_file.exists() and weights_file.exists():
            return str(root_models)
        return None

    # HF‑логика удалена: приложение использует только локальные модели
    
    def _extract_words(self, segments: list) -> list:
        """
        Извлекает слова с временными метками из сегментов
        
        Args:
            segments: Список сегментов от Whisper
            
        Returns:
            Список слов с временными метками
        """
        words = []
        for segment in segments:
            if "words" in segment:
                for word in segment["words"]:
                    words.append({
                        "word": word.get("word", "").strip(),
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                        "confidence": word.get("probability", 0)
                    })
        return words
    
    def _remove_repetitions(self, text: str) -> str:
        """
        Удаляет циклические повторения из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный от повторений текст
        """
        try:
            if not text or len(text) < 50:
                return text
            
            # Разбиваем на предложения
            sentences = text.split('.')
            clean_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Если предложение повторяется более 2 раз подряд - удаляем
                if len(clean_sentences) >= 2:
                    if (
                        clean_sentences[-1].strip() == sentence
                        and clean_sentences[-2].strip() == sentence
                    ):
                        # Пропускаем повторяющееся предложение
                        continue
                
                clean_sentences.append(sentence)
            
            # Собираем обратно
            result = '. '.join(clean_sentences)
            if result and not result.endswith('.'):
                result += '.'
                
            # Дополнительная очистка: удаляем повторы слов
            result = self._remove_word_repetitions(result)
            
            return result.strip()
            
        except Exception as e:
            self.logger.warning(f"Ошибка очистки повторений: {e}")
            return text
    
    def _remove_word_repetitions(self, text: str) -> str:
        """Удаляет повторения слов/фраз - УЛУЧШЕННАЯ ВЕРСИЯ"""
        try:
            words = text.split()
            if len(words) < 10:
                return text
            
            clean_words = []
            i = 0
            
            # Проверяем повторения фраз разной длины
            while i < len(words):
                found_repetition = False
                
                # Ищем фразы от 5 до 15 слов (длинные фразы сначала)
                for phrase_len in range(15, 2, -1):
                    if i + phrase_len > len(words):
                        continue
                        
                    phrase = ' '.join(words[i:i+phrase_len])
                    
                    # Считаем повторения подряд
                    repetitions = 0
                    pos = i
                    while (pos + phrase_len <= len(words) and 
                           ' '.join(words[pos:pos+phrase_len]) == phrase):
                        repetitions += 1
                        pos += phrase_len
                    
                    # Если фраза повторяется более 1 раза - оставляем только одну
                    if repetitions > 1:
                        clean_words.extend(words[i:i+phrase_len])
                        i = pos  # Пропускаем все повторения
                        found_repetition = True
                        msg = f"Удалено {repetitions-1} повторений фразы"
                        self.logger.info(f"{msg}: '{phrase[:50]}...'")
                        break
                
                # Если повторений не найдено - добавляем слово
                if not found_repetition:
                    clean_words.append(words[i])
                    i += 1
            
            return ' '.join(clean_words)
            
        except Exception as e:
            self.logger.warning(f"Ошибка очистки повторений слов: {e}")
            return text

    def _calculate_confidence(self, segments: list) -> float:
        """
        Вычисляет среднюю уверенность распознавания
        
        Args:
            segments: Список сегментов от Whisper
            
        Returns:
            Средняя уверенность (от 0 до 1)
        """
        if not segments:
            return 0.0
        
        total_confidence = 0.0
        word_count = 0
        
        for segment in segments:
            if "words" in segment:
                for word in segment["words"]:
                    total_confidence += word.get("probability", 0)
                    word_count += 1
        
        return total_confidence / word_count if word_count > 0 else 0.0 