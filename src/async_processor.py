"""
Синхронный процессор для обработки речи
ВНИМАНИЕ: MLX Whisper НЕ поддерживает параллельные вызовы!
"""

import logging
import numpy as np
import gc
from typing import Optional, Callable, Tuple


class AsyncSpeechProcessor:
    """Синхронный процессор для обработки речи"""
    
    def __init__(self, whisper_service, punctuation_service,
                 max_workers=2):
        self.logger = logging.getLogger(__name__)
        self.whisper_service = whisper_service
        self.punctuation_service = punctuation_service

        # 🆕 Полностью синхронная обработка без multiprocessing
        self.logger.info("SpeechProcessor инициализирован (синхронный режим)")

    def process_audio_parallel(
        self,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Синхронная обработка аудио

        Args:
            audio_data: Аудио данные
            progress_callback: Колбэк для отчета о прогрессе

        Returns:
            Tuple[распознанный_текст, резюме_llm]
        """
        try:
            self.logger.info("🚀 Запуск обработки речи")

            if progress_callback:
                progress_callback("🎯 Распознавание речи...")

            # Этап 1: Whisper - синхронно
            transcribed_text = self._sync_transcribe(audio_data)

            if not transcribed_text.strip():
                return "", None

            # Этап 2: Постобработка - синхронно
            if progress_callback:
                progress_callback("⚡ Постобработка текста...")

            # Пунктуация
            punctuated_text = self._sync_punctuation(transcribed_text)

            # 🆕 Принудительная очистка памяти
            self._cleanup_memory()

            self.logger.info("✅ Обработка завершена")
            return punctuated_text, None

        except Exception as e:
            self.logger.error(f"Ошибка обработки: {e}")
            # 🆕 Очистка памяти даже при ошибке
            self._cleanup_memory()
            return "", None

    def _sync_transcribe(self, audio_data: np.ndarray) -> str:
        """Синхронная транскрипция"""
        try:
            result = self.whisper_service.transcribe(audio_data)
            text = result.get("text", "") if isinstance(result, dict) else result
            preview = text[:50] if text else "пусто"
            self.logger.info(f"Whisper результат: '{preview}...'")
            return text
        except Exception as e:
            self.logger.error(f"Ошибка Whisper: {e}")
            return ""

    def _sync_punctuation(self, text: str) -> str:
        """Синхронная обработка пунктуации"""
        try:
            return self.punctuation_service.restore_punctuation(text)
        except Exception as e:
            self.logger.error(f"Ошибка восстановления пунктуации: {e}")
            return text
    
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
        Синхронная обработка аудио
        Используется из основного приложения
        """
        # 🆕 Прямая синхронная обработка без asyncio
        return self.process_audio_parallel(audio_data, progress_callback)