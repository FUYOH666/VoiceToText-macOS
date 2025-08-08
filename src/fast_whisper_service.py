"""
Оптимизированный Whisper сервис с кэшированием и ускорением
"""

import logging
import numpy as np
import threading
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
import mlx_whisper
from concurrent.futures import ThreadPoolExecutor


class FastWhisperService:
    """Ускоренный сервис распознавания речи"""
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_lock = threading.Lock()
        
        # Кэширование
        self.cache_enabled = True
        self.cache_dir = Path("cache/transcriptions")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Пул потоков для параллельной обработки
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Предзагружаем модель в фоне
        self._preload_model()
    
    def _preload_model(self):
        """Предварительная загрузка модели в фоновом потоке"""
        def load_model():
            try:
                with self.model_lock:
                    if self.model is None:
                        self.logger.info("Предзагрузка MLX Whisper модели...")
                        # Загружаем модель один раз
                        self.model = mlx_whisper.load_model(
                            str(self.config.models["whisper"]["path"])
                        )
                        self.logger.info("Модель предзагружена успешно")
            except Exception as e:
                self.logger.error(f"Ошибка предзагрузки модели: {e}")
        
        # Запускаем в отдельном потоке
        threading.Thread(target=load_model, daemon=True).start()
    
    def _get_cache_key(self, audio_data: np.ndarray) -> str:
        """Генерирует ключ кэша для аудио данных"""
        # Создаем хэш от первых и последних 1000 сэмплов + длины
        if len(audio_data) > 2000:
            sample_data = np.concatenate([
                audio_data[:1000], 
                audio_data[-1000:]
            ])
        else:
            sample_data = audio_data
        
        # Хэшируем с учетом длины
        hash_input = f"{len(audio_data)}_{sample_data.tobytes()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получает результат из кэша"""
        if not self.cache_enabled:
            return None
        
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.logger.debug(f"Найден кэш для {cache_key}")
                    return json.load(f)
        except Exception as e:
            self.logger.debug(f"Ошибка чтения кэша: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """Сохраняет результат в кэш"""
        if not self.cache_enabled:
            return
        
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Результат сохранен в кэш: {cache_key}")
        except Exception as e:
            self.logger.debug(f"Ошибка сохранения в кэш: {e}")
    
    def transcribe_fast(
        self, 
        audio_data: np.ndarray, 
        language: str = "ru"
    ) -> Dict[str, Any]:
        """
        Быстрое распознавание с кэшированием
        
        Args:
            audio_data: Аудио данные
            language: Язык распознавания
            
        Returns:
            Результат распознавания
        """
        try:
            # Проверяем кэш
            cache_key = self._get_cache_key(audio_data)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                self.logger.info("Использован кэшированный результат")
                return cached_result
            
            # Ждем загрузки модели
            self._ensure_model_loaded()
            
            duration = len(audio_data) / 16000
            self.logger.info(f"Быстрое распознавание: {duration:.2f}с")
            
            # Оптимизированные параметры для скорости
            with self.model_lock:
                result = mlx_whisper.transcribe(
                    audio=audio_data,
                    model=self.model,
                    language=language,
                    temperature=0.0,  # Детерминистичность
                    compression_ratio_threshold=2.4,
                    logprob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False,  # Ускорение
                    word_timestamps=False,  # Ускорение
                    verbose=False
                )
            
            # Форматируем результат
            formatted_result = {
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "duration": duration,
                "confidence": self._estimate_confidence(result),
                "cached": False
            }
            
            # Сохраняем в кэш
            self._save_to_cache(cache_key, formatted_result)
            
            self.logger.info(f"Распознавание завершено: "
                           f"{formatted_result['text'][:50]}...")
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Ошибка быстрого распознавания: {e}")
            # Возвращаем пустой результат
            return {
                "text": "",
                "language": language,
                "duration": len(audio_data) / 16000,
                "confidence": 0.0,
                "cached": False,
                "error": str(e)
            }
    
    def _ensure_model_loaded(self):
        """Убеждается что модель загружена"""
        max_wait = 30  # Максимум 30 секунд ожидания
        wait_step = 0.1
        waited = 0
        
        while self.model is None and waited < max_wait:
            if waited == 0:
                self.logger.info("Ожидание загрузки модели...")
            time.sleep(wait_step)
            waited += wait_step
        
        if self.model is None:
            raise RuntimeError("Модель не загружена за отведенное время")
    
    def _estimate_confidence(self, result: Dict) -> float:
        """Оценивает уверенность распознавания"""
        try:
            # Простая эвристика на основе длины текста
            text = result.get("text", "")
            if not text.strip():
                return 0.0
            
            # Базовая уверенность 0.8 для непустого текста
            base_confidence = 0.8
            
            # Бонус за длину текста
            length_bonus = min(0.15, len(text) / 100)
            
            return min(0.95, base_confidence + length_bonus)
            
        except Exception:
            return 0.5
    
    def clear_cache(self):
        """Очищает кэш транскрипций"""
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("Кэш очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Возвращает статистику кэша"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "files": len(cache_files),
                "size_mb": round(total_size / 1024 / 1024, 2)
            }
        except Exception:
            return {"files": 0, "size_mb": 0}
    
    def __del__(self):
        """Очистка ресурсов"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 