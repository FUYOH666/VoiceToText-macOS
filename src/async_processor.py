"""
Синхронный процессор для обработки речи
ВНИМАНИЕ: MLX Whisper НЕ поддерживает параллельные вызовы!
"""

import logging
import numpy as np
import gc
from typing import Optional, Callable, Tuple, Any


class AsyncSpeechProcessor:
    """Синхронный процессор для обработки речи с поддержкой длинных записей"""

    def __init__(self, whisper_service, punctuation_service,
                 config: Any, max_workers=2):
        self.logger = logging.getLogger(__name__)
        self.whisper_service = whisper_service
        self.punctuation_service = punctuation_service
        self.config = config

        # Параметры для обработки длинных записей из конфигурации
        chunk_config = config.performance.get("chunk_processing", {})
        self.chunk_enabled = chunk_config.get("enabled", True)
        self.chunk_duration_sec = chunk_config.get("max_chunk_duration_sec", 300)
        self.chunk_overlap_sec = chunk_config.get("chunk_overlap_sec", 5)
        self.max_memory_mb = config.performance.get("memory_limit_mb", 1024)

        self.logger.info(f"SpeechProcessor инициализирован (синхронный режим, чанки: {self.chunk_enabled})")
        self.logger.info(f"Параметры чанков: {self.chunk_duration_sec}сек, перекрытие {self.chunk_overlap_sec}сек")

    def process_audio_parallel(
        self,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Синхронная обработка аудио с поддержкой длинных записей

        Args:
            audio_data: Аудио данные
            progress_callback: Колбэк для отчета о прогрессе

        Returns:
            Tuple[распознанный_текст, резюме_llm]
        """
        try:
            self.logger.info("🚀 Запуск обработки речи")

            # Определяем длительность аудио
            duration_sec = len(audio_data) / 16000
            self.logger.info(f"Длительность аудио: {duration_sec:.1f} секунд")

            # Проверяем, нужно ли разбивать на чанки
            if self.chunk_enabled and duration_sec > self.chunk_duration_sec:
                self.logger.info("🎯 Длинная запись - используем чанковую обработку")
                return self._process_long_audio(audio_data, progress_callback)
            else:
                self.logger.info("🎯 Короткая/средняя запись - прямая обработка")
                return self._process_short_audio(audio_data, progress_callback)

        except Exception as e:
            self.logger.error(f"Ошибка обработки: {e}")
            # 🆕 Очистка памяти даже при ошибке
            self._cleanup_memory()
            return "", None

    def _process_short_audio(
        self,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """Обработка коротких записей (менее 5 минут)"""
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

    def _process_long_audio(
        self,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[str]]:
        """Обработка длинных записей по чанкам"""
        try:
            self.logger.info("🎯 Начинаем чанковую обработку длинного аудио")

            # Разбиваем аудио на чанки
            chunks = self._split_audio_into_chunks(audio_data)
            self.logger.info(f"📦 Аудио разбито на {len(chunks)} чанков")

            combined_text = []
            total_chunks = len(chunks)

            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_msg = f"🎯 Обработка чанка {i+1}/{total_chunks}..."
                    progress_callback(progress_msg)

                self.logger.info(f"📝 Обрабатываем чанк {i+1}/{total_chunks}")

                # Обрабатываем чанк
                chunk_result = self._process_short_audio(chunk, None)

                if chunk_result and chunk_result[0].strip():
                    combined_text.append(chunk_result[0].strip())

                # Очистка памяти между чанками
                self._cleanup_memory()

            # Объединяем результаты
            if combined_text:
                final_text = " ".join(combined_text)

                # Финальная постобработка
                if progress_callback:
                    progress_callback("⚡ Финальная постобработка...")

                final_text = self._sync_punctuation(final_text)

                self.logger.info(f"✅ Длинная запись обработана: {len(final_text)} символов")
                return final_text, None
            else:
                self.logger.warning("Не удалось обработать ни один чанк")
                return "", None

        except Exception as e:
            self.logger.error(f"Ошибка обработки длинного аудио: {e}")
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
    
    def _split_audio_into_chunks(self, audio_data: np.ndarray) -> list:
        """
        Разбивает длинное аудио на чанки с перекрытием

        Args:
            audio_data: Исходные аудио данные

        Returns:
            Список чанков (список numpy массивов)
        """
        try:
            sample_rate = 16000
            chunk_samples = int(self.chunk_duration_sec * sample_rate)
            overlap_samples = int(self.chunk_overlap_sec * sample_rate)

            total_samples = len(audio_data)
            chunks = []

            start_sample = 0

            while start_sample < total_samples:
                # Определяем конец чанка
                end_sample = min(start_sample + chunk_samples, total_samples)

                # Вырезаем чанк
                chunk = audio_data[start_sample:end_sample]
                chunks.append(chunk)

                self.logger.debug(f"Чанк {len(chunks)}: {start_sample}-{end_sample} сэмплов "
                                f"({len(chunk)/sample_rate:.1f} сек)")

                # Переходим к следующему чанку с учетом перекрытия
                if end_sample >= total_samples:
                    break

                start_sample = end_sample - overlap_samples

                # Если следующий чанк будет слишком маленьким, включаем его в текущий
                if total_samples - start_sample < chunk_samples * 0.3:
                    break

            self.logger.info(f"Аудио разбито на {len(chunks)} чанков")
            return chunks

        except Exception as e:
            self.logger.error(f"Ошибка разбиения аудио на чанки: {e}")
            # Возвращаем оригинальный аудио как один чанк
            return [audio_data]

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