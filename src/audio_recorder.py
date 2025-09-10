"""
Модуль для записи аудио с микрофона
"""

import logging
import numpy as np
import pyaudio
import time
import gc
from typing import Any, Callable, Optional
from collections import deque


class AudioRecorder:
    """Класс для записи аудио с микрофона"""
    
    def __init__(self, config: Any):
        """
        Инициализация аудио рекордера
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Аудио параметры
        self.sample_rate = config.audio["sample_rate"]
        self.chunk_size = 4096  # 🔥 Увеличено с 1024 до 4096 для лучшей производительности на M4 Max
        self.channels = 1  # Моно
        self.format = pyaudio.paFloat32
        
        # 🆕 Параметры для длинных записей
        max_duration_key = "max_recording_duration"
        # 0 = без лимита
        self.max_duration = config.audio.get(max_duration_key, 0)
        cleanup_key = "buffer_cleanup_after_processing"
        self.cleanup_after_processing = config.audio.get(cleanup_key, True)
        
        # Состояние записи
        self.is_recording = False
        self.audio_data = deque()
        self.recording_thread = None
        self.last_recording = None
        
        # PyAudio объект
        self.audio = None
        self.stream = None
        
        # Callback для обработки аудио
        self.audio_callback: Optional[Callable] = None
        
        self._init_audio()
    
    def _init_audio(self):
        """Инициализирует PyAudio"""
        try:
            self.audio = pyaudio.PyAudio()
            self.logger.info("PyAudio инициализирован")
            
            # Показываем доступные устройства
            self._list_audio_devices()
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации PyAudio: {e}")
            raise
    
    def _list_audio_devices(self):
        """Показывает список доступных аудио устройств"""
        try:
            device_count = self.audio.get_device_count()
            msg = f"Найдено {device_count} аудио устройств:"
            self.logger.info(msg)
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    device_name = device_info['name']
                    input_channels = device_info['maxInputChannels']
                    device_msg = f"  {i}: {device_name} (входы: {input_channels})"
                    self.logger.info(device_msg)
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения списка устройств: {e}")
    
    def start_recording(self, callback: Optional[Callable] = None):
        """
        Начинает запись аудио

        Args:
            callback: Функция обратного вызова для обработки аудио данных
        """
        try:
            if self.is_recording:
                self.logger.warning("Запись уже идет")
                return

            # 🔧 Проверяем инициализацию PyAudio (только один раз)
            if self.audio is None:
                self._init_audio()

            self.audio_callback = callback
            self.audio_data.clear()

            # Открываем поток
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )

            self.is_recording = True
            self.stream.start_stream()

            # 🔧 Логируем настройки записи
            if self.max_duration > 0:
                msg = f"Запись аудио начата (макс. {self.max_duration}с)"
                self.logger.info(msg)
            else:
                no_limit_msg = "Запись аудио начата (без лимита по времени)"
                self.logger.info(no_limit_msg)

        except Exception as e:
            self.logger.error(f"Ошибка начала записи: {e}")
            # 🔧 Безопасная очистка при ошибке
            try:
                if self.stream:
                    self.stream.close()
                    self.stream = None
            except Exception:
                pass
            raise
    

    
    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Останавливает запись и возвращает аудио данные

        Returns:
            Массив аудио данных или None при ошибке
        """
        try:
            if not self.is_recording:
                self.logger.warning("Запись не активна")
                return None

            self.is_recording = False

            # 🔧 Закрываем только поток, но НЕ завершаем PyAudio!
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            # Собираем аудио данные
            if self.audio_data:
                audio_array = np.concatenate(list(self.audio_data))
                # Сохраняем последнюю запись
                self.last_recording = audio_array

                duration = len(audio_array) / self.sample_rate
                duration_msg = f"Запись остановлена, длина: {duration:.2f}с"
                self.logger.info(duration_msg)

                # 🔧 Очищаем буфер если включена настройка
                if self.cleanup_after_processing:
                    self._cleanup_buffer()

                return audio_array
            else:
                self.logger.warning("Нет аудио данных")
                return None

        except Exception as e:
            self.logger.error(f"Ошибка остановки записи: {e}")
            return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback функция для обработки аудио данных
        
        Args:
            in_data: Входные аудио данные
            frame_count: Количество фреймов
            time_info: Информация о времени
            status: Статус потока
            
        Returns:
            Tuple для PyAudio
        """
        try:
            if self.is_recording:
                # Преобразуем в numpy array
                audio_chunk = np.frombuffer(in_data, dtype=np.float32)
                
                # Сохраняем данные
                self.audio_data.append(audio_chunk)
                
                # 🆕 Проверяем лимит только если он установлен
                if self.max_duration > 0:
                    current_chunks = len(self.audio_data) * self.chunk_size
                    current_duration = current_chunks / self.sample_rate
                    if current_duration > self.max_duration:
                        limit_msg = (f"Достигнут лимит записи "
                                   f"{self.max_duration}с")
                        self.logger.warning(limit_msg)
                        # Можно автоматически остановить запись
                        # или просто предупредить
                        # self.is_recording = False  # Для автостопа
                
                # Вызываем callback если есть
                if self.audio_callback:
                    try:
                        self.audio_callback(audio_chunk)
                    except Exception as e:
                        callback_err = f"Ошибка в audio callback: {e}"
                        self.logger.error(callback_err)
            
            return (in_data, pyaudio.paContinue)
            
        except Exception as e:
            self.logger.error(f"Ошибка в audio callback: {e}")
            return (in_data, pyaudio.paContinue)
    
    def _cleanup_buffer(self):
        """🆕 Принудительная очистка аудио буфера"""
        try:
            self.audio_data.clear()
            if hasattr(self, 'last_recording'):
                self.last_recording = None
            gc.collect()  # Принудительная сборка мусора
            self.logger.debug("Аудио буфер очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки буфера: {e}")
    
    def get_current_audio(self) -> Optional[np.ndarray]:
        """
        Возвращает текущие аудио данные без остановки записи
        
        Returns:
            Массив текущих аудио данных
        """
        try:
            if self.audio_data:
                return np.concatenate(list(self.audio_data))
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения текущих данных: {e}")
            return None
    
    def record_for_duration(self, duration: float) -> Optional[np.ndarray]:
        """
        Записывает аудио в течение указанного времени
        
        Args:
            duration: Длительность записи в секундах
            
        Returns:
            Массив аудио данных
        """
        try:
            self.start_recording()
            time.sleep(duration)
            return self.stop_recording()
            
        except Exception as e:
            self.logger.error(f"Ошибка записи по времени: {e}")
            return None
    
    def cleanup(self):
        """Очищает ресурсы"""
        try:
            if self.is_recording:
                self.stop_recording()

            # 🔧 Очищаем только буферы, но сохраняем PyAudio
            self._cleanup_buffer()

            # 🔧 НЕ завершаем PyAudio - он должен жить в течение всего приложения
            # if self.audio:
            #     self.audio.terminate()
            #     self.audio = None

            self.logger.info("Аудио рекордер очищен (PyAudio сохранен)")

        except Exception as e:
            self.logger.error(f"Ошибка очистки рекордера: {e}")
    
    def __del__(self):
        """Деструктор - завершает PyAudio"""
        try:
            if self.is_recording:
                self.stop_recording()

            # 🔧 В деструкторе завершаем PyAudio окончательно
            if self.audio:
                self.audio.terminate()
                self.audio = None

            self.logger.debug("AudioRecorder полностью уничтожен")

        except Exception:
            # Игнорируем ошибки в деструкторе
            pass 