"""
Асинхронный процессор для ускоренной обработки речи
ВНИМАНИЕ: MLX Whisper НЕ поддерживает параллельные вызовы!
"""

import asyncio
import logging
import numpy as np
import gc
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Tuple


class AsyncSpeechProcessor:
    """Асинхронный процессор для ускорения постобработки"""
    
    def __init__(self, whisper_service, punctuation_service, 
                 max_workers=2):
        self.logger = logging.getLogger(__name__)
        self.whisper_service = whisper_service
        self.punctuation_service = punctuation_service
        
        # 🆕 Убираем ThreadPoolExecutor для избежания конфликтов semaphore
        # Основная обработка будет происходить через asyncio
        self.logger.info("AsyncSpeechProcessor инициализирован (без ThreadPoolExecutor)")
        
    async def process_audio_parallel(
        self, 
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Обработка аудио с async оптимизацией постобработки
        
        Args:
            audio_data: Аудио данные
            progress_callback: Колбэк для отчета о прогрессе
            
        Returns:
            Tuple[распознанный_текст, резюме_llm]
        """
        try:
            self.logger.info("🚀 Запуск оптимизированной обработки")
            
            if progress_callback:
                progress_callback("🎯 Распознавание речи...")
            
            # Этап 1: Whisper - последовательно (MLX ограничение)
            transcribed_text = await self._async_transcribe(audio_data)
            
            if not transcribed_text.strip():
                return "", None
            
            # Этап 2: Параллельная постобработка (пунктуация)
            if progress_callback:
                progress_callback("⚡ Параллельная постобработка...")
            
            # Запускаем пунктуацию
            punctuated_text = await self._async_punctuation(transcribed_text)
            
            # 🆕 Принудительная очистка памяти
            self._cleanup_memory()
            
            self.logger.info("✅ Оптимизированная обработка завершена")
            return punctuated_text, None
            
        except Exception as e:
            self.logger.error(f"Ошибка оптимизированной обработки: {e}")
            # 🆕 Очистка памяти даже при ошибке
            self._cleanup_memory()
            return "", None
    
    async def _async_transcribe(self, audio_data: np.ndarray) -> str:
        """Асинхронная транскрипция (один вызов Whisper)"""
        loop = asyncio.get_event_loop()
        
        def transcribe():
            try:
                result = self.whisper_service.transcribe(audio_data)
                text = result.get("text", "") if isinstance(result, dict) else result
                preview = text[:50] if text else "пусто"
                self.logger.info(f"Whisper результат: '{preview}...'")
                return text
            except Exception as e:
                self.logger.error(f"Ошибка Whisper: {e}")
                return ""
        
        return await loop.run_in_executor(None, transcribe)
    
    async def _async_punctuation(self, text: str) -> str:
        """Асинхронная обработка пунктуации"""
        loop = asyncio.get_event_loop()
        
        def restore_punctuation():
            try:
                return self.punctuation_service.restore_punctuation(text)
            except Exception as e:
                self.logger.error(f"Ошибка восстановления пунктуации: {e}")
                return text
        
        return await loop.run_in_executor(None, restore_punctuation)
    
    def _cleanup_memory(self):
        """🆕 Принудительная очистка памяти после обработки"""
        try:
            gc.collect()
            self.logger.debug("Память AsyncProcessor очищена")
        except Exception as e:
            self.logger.error(f"Ошибка очистки памяти AsyncProcessor: {e}")
    
    def process_audio_sync(
        self,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Синхронная обертка для async обработки
        Используется из основного приложения
        """
        # 🆕 Упрощенная синхронная обработка без лишних ThreadPoolExecutor
        try:
            # Создаем новый event loop для безопасной работы
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.process_audio_parallel(audio_data, progress_callback)
                )
            finally:
                # Гарантированная очистка
                try:
                    loop.close()
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Ошибка синхронной обработки: {e}")
            return "", None