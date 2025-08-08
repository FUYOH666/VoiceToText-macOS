"""
Сервис обнаружения речи (Voice Activity Detection) через Silero VAD
"""

import logging
import numpy as np
import torch
from typing import Any, List, Tuple
from pathlib import Path


class VADService:
    """Сервис для обнаружения речи в аудио"""
    
    def __init__(self, config: Any):
        """
        Инициализация VAD сервиса
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.get_speech_timestamps = None
        self.sample_rate = 16000
        # Lazy-load to save memory until needed
        try:
            lazy = self.config.models.get("vad", {}).get("lazy_load", True)
        except Exception:
            lazy = True

        if not lazy:
            self._load_model()
    
    def _load_model(self):
        """Загружает модель Silero VAD"""
        try:
            cache_dir = Path(self.config.models["vad"]["cache_dir"])
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Загрузка Silero VAD модели...")
            
            # Загружаем предобученную модель Silero VAD с utils
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True
            )
            
            # Извлекаем функции из utils tuple
            (self.get_speech_timestamps, 
             _, 
             self.read_audio, 
             _, 
             _) = utils
            
            self.logger.info("Silero VAD модель успешно загружена")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки VAD модели: {e}")
            raise
    
    def detect_speech(
        self, 
        audio_data: np.ndarray, 
        threshold: float = None
    ) -> List[dict]:
        """
        Обнаруживает сегменты речи в аудио
        
        Args:
            audio_data: Аудио данные (16kHz, моно)
            threshold: Порог обнаружения речи (по умолчанию из конфига)
            
        Returns:
            Список сегментов речи с временными метками
        """
        try:
            if self.model is None:
                # Lazy init on first use
                self._load_model()
                if self.model is None:
                    raise RuntimeError("VAD модель не загружена")
            
            if threshold is None:
                threshold = self.config.audio["vad_threshold"]
            
            # Преобразуем numpy array в torch tensor
            if isinstance(audio_data, np.ndarray):
                audio_tensor = torch.from_numpy(audio_data).float()
            else:
                audio_tensor = audio_data
            
            # Получаем вероятности речи
            speech_timestamps = self._get_speech_timestamps(
                audio_tensor, 
                threshold
            )
            
            # Форматируем результат
            segments = []
            for timestamp in speech_timestamps:
                segments.append({
                    "start": timestamp["start"] / self.sample_rate,
                    "end": timestamp["end"] / self.sample_rate,
                    "confidence": timestamp.get("confidence", 1.0)
                })
            
            self.logger.info(f"Обнаружено {len(segments)} сегментов речи")
            return segments
            
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения речи: {e}")
            raise
    
    def _get_speech_timestamps(
        self, 
        audio: torch.Tensor, 
        threshold: float
    ) -> List[dict]:
        """
        Получает временные метки речи из аудио
        
        Args:
            audio: Аудио тензор
            threshold: Порог обнаружения
            
        Returns:
            Список временных меток
        """
        try:
            if self.get_speech_timestamps is None:
                raise RuntimeError(
                    "get_speech_timestamps функция не загружена"
                )
                
            # Используем функцию для получения временных меток
            speech_timestamps = self.get_speech_timestamps(
                audio, 
                self.model,
                threshold=threshold,
                min_speech_duration_ms=250,
                min_silence_duration_ms=100,
                window_size_samples=1536,
                speech_pad_ms=30
            )
            
            return speech_timestamps
            
        except Exception as e:
            self.logger.error(f"Ошибка получения временных меток: {e}")
            return []
    
    def is_speech(
        self, 
        audio_chunk: np.ndarray, 
        threshold: float = None
    ) -> bool:
        """
        Проверяет содержит ли аудио фрагмент речь
        
        Args:
            audio_chunk: Фрагмент аудио
            threshold: Порог обнаружения
            
        Returns:
            True если обнаружена речь
        """
        try:
            if threshold is None:
                threshold = self.config.audio["vad_threshold"]
            
            # Преобразуем в тензор
            if isinstance(audio_chunk, np.ndarray):
                audio_tensor = torch.from_numpy(audio_chunk).float()
            else:
                audio_tensor = audio_chunk
            
            # Получаем вероятность речи
            speech_prob = self.model(audio_tensor, self.sample_rate).item()
            
            return speech_prob > threshold
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки речи: {e}")
            return False
    
    def split_by_silence(
        self, 
        audio_data: np.ndarray, 
        max_chunk_duration: float = 30.0
    ) -> List[Tuple[np.ndarray, float, float]]:
        """
        Разделяет аудио на фрагменты по паузам
        
        Args:
            audio_data: Исходные аудио данные
            max_chunk_duration: Максимальная длина фрагмента в секундах
            
        Returns:
            Список кортежей (аудио_фрагмент, начало, конец)
        """
        try:
            # Обнаруживаем сегменты речи
            speech_segments = self.detect_speech(audio_data)
            
            if not speech_segments:
                duration = len(audio_data) / self.sample_rate
                return [(audio_data, 0.0, duration)]
            
            chunks = []
            for segment in speech_segments:
                start_sample = int(segment["start"] * self.sample_rate)
                end_sample = int(segment["end"] * self.sample_rate)
                
                # Извлекаем фрагмент
                chunk = audio_data[start_sample:end_sample]
                
                # Разбиваем длинные фрагменты
                if len(chunk) > max_chunk_duration * self.sample_rate:
                    # Разбиваем на части
                    chunk_size = int(max_chunk_duration * self.sample_rate)
                    for i in range(0, len(chunk), chunk_size):
                        sub_chunk = chunk[i:i + chunk_size]
                        sub_start = segment["start"] + i / self.sample_rate
                        sub_end = min(
                            segment["end"], 
                            sub_start + len(sub_chunk) / self.sample_rate
                        )
                        chunks.append((sub_chunk, sub_start, sub_end))
                else:
                    chunks.append((chunk, segment["start"], segment["end"]))
            
            self.logger.info(f"Аудио разделено на {len(chunks)} фрагментов")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Ошибка разделения аудио: {e}")
            duration = len(audio_data) / self.sample_rate
            return [(audio_data, 0.0, duration)]
    
    def has_speech(self, audio_data: np.ndarray, threshold: float = None) -> bool:
        """
        Проверяет содержит ли аудио речь (для длинных записей)
        
        Args:
            audio_data: Аудио данные любой длины
            threshold: Порог обнаружения
            
        Returns:
            True если обнаружена речь
        """
        try:
            segments = self.detect_speech(audio_data, threshold)
            return len(segments) > 0
        except Exception as e:
            self.logger.error(f"Ошибка проверки наличия речи: {e}")
            return False 