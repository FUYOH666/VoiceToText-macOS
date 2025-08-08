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
                 llm_service=None, max_workers=2):
        self.logger = logging.getLogger(__name__)
        self.whisper_service = whisper_service
        self.punctuation_service = punctuation_service
        self.llm_service = llm_service
        
        # 🆕 Ограничиваем количество потоков из конфигурации
        config_workers = getattr(whisper_service, 'config', None)
        if config_workers and hasattr(config_workers, 'performance'):
            max_workers = config_workers.performance.get(
                'max_concurrent_threads', max_workers
            )
        
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sw-worker")
        self.logger.info(f"AsyncSpeechProcessor с {max_workers} потоками")
        
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
            
            # Этап 2: Параллельная постобработка (пунктуация + LLM)
            if progress_callback:
                progress_callback("⚡ Параллельная постобработка...")
            
            # Запускаем пунктуацию и LLM параллельно
            tasks = [
                self._async_punctuation(transcribed_text)
            ]
            
            # LLM только если включен
            llm_enabled = (self.llm_service and 
                hasattr(self.llm_service, 'enabled') and 
                         getattr(self.llm_service, 'enabled', False))
            
            if llm_enabled:
                tasks.append(self._async_llm_summary(transcribed_text))
            else:
                tasks.append(self._dummy_llm())
            
            punctuated_text, llm_summary = await asyncio.gather(*tasks)
            
            # 🆕 Принудительная очистка памяти
            self._cleanup_memory()
            
            self.logger.info("✅ Оптимизированная обработка завершена")
            return punctuated_text, llm_summary
            
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
        
        return await loop.run_in_executor(self.executor, transcribe)
    
    async def _async_punctuation(self, text: str) -> str:
        """Асинхронная обработка пунктуации"""
        loop = asyncio.get_event_loop()
        
        def restore_punctuation():
            try:
                return self.punctuation_service.restore_punctuation(text)
            except Exception as e:
                self.logger.error(f"Ошибка восстановления пунктуации: {e}")
                return text
        
        return await loop.run_in_executor(self.executor, restore_punctuation)
    
    async def _async_llm_summary(self, text: str) -> Optional[str]:
        """Асинхронная генерация LLM резюме"""
        loop = asyncio.get_event_loop()
        
        def generate_summary():
            try:
                if not self.llm_service:
                    return None
                return self.llm_service.generate_summary(text)
            except Exception as e:
                self.logger.error(f"Ошибка LLM резюме: {e}")
                return None
        
        return await loop.run_in_executor(self.executor, generate_summary)
    
    async def _dummy_llm(self) -> Optional[str]:
        """Заглушка для LLM если не включен"""
        return None
    
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
        # 🆕 Правильное управление event loop
        loop = None
        try:
            # Пробуем получить текущий loop
            try:
                loop = asyncio.get_running_loop()
                # Если loop уже запущен, используем новый поток
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, 
                                           audio_data, progress_callback)
                    return future.result()
            except RuntimeError:
                # Нет запущенного loop, создаем новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    self.process_audio_parallel(audio_data, progress_callback)
                )
        except Exception as e:
            self.logger.error(f"Ошибка синхронной обработки: {e}")
            return "", None
        finally:
            # 🆕 Правильная очистка loop
            if loop and not loop.is_running():
                try:
                    loop.close()
                except Exception:
                    pass
    
    def _run_in_new_loop(self, audio_data: np.ndarray,
                        progress_callback: Optional[Callable] = None):
        """Запуск в новом event loop (для threading)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.process_audio_parallel(audio_data, progress_callback)
            )
        finally:
            loop.close()
    
    def cleanup(self):
        """🆕 Явная очистка ресурсов"""
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=True)
                self.executor = None
            self._cleanup_memory()
            self.logger.info("AsyncProcessor очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки AsyncProcessor: {e}")
    
    def __del__(self):
        """Cleanup при удалении объекта"""
        try:
            self.cleanup()
        except Exception:
            pass 