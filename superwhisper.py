"""
SuperWhisper Local - простая автовставка транскрипции
"""

import os
import sys
import logging
import threading
import time
import rumps
import pyperclip

# Добавляем src в PATH (разрешено в начале модуля)
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.config import Config  # noqa: E402
from src.audio_recorder import AudioRecorder  # noqa: E402
from src.whisper_service import WhisperService  # noqa: E402
from src.punctuation_service import PunctuationService  # noqa: E402
from src.notification_service import NotificationService  # noqa: E402
from src.hotkey_manager import HotkeyManager  # noqa: E402
from src.auto_paste import AutoPasteService  # noqa: E402
from src.memory_manager import free_memory, log_process_memory  # noqa: E402
from src.async_processor import AsyncSpeechProcessor  # noqa: E402


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


class ProgressStates:
    """🆕 Состояния прогресса с анимированными иконками"""
    IDLE = ("🎤", "Готов к записи")
    RECORDING = ("🔴", "Запись... {time}")
    PROCESSING = ("⏳", "Обработка аудио...")
    TRANSCRIBING = ("🧠", "Распознавание речи...")
    PUNCTUATING = ("✏️", "Расстановка пунктуации...")
    FINALIZING = ("✅", "Завершение...")


class SuperWhisperSimple(rumps.App):
    """Упрощённое приложение SuperWhisper с автовставкой"""
    
    def __init__(self, config: Config):
        super().__init__("SuperWhisper", title="🎤")
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Состояние
        self.is_recording = False
        self.is_processing = False
        self.last_text = ""
        self.recording_start_time = None
        self.recording_timer = None

        # Настройки автовставки
        self.use_clipboard_paste = True  # По умолчанию через буфер обмена
        
        # Инициализация
        self._init_services()
        self._create_menu()
        self._start_hotkeys()
        
        self.logger.info("SuperWhisper Simple запущен")
    
    def _init_services(self):
        """Инициализация всех сервисов"""
        try:
            # Основные сервисы
            self.whisper_service = WhisperService(self.config)
            self.punctuation_service = PunctuationService(self.config)
            self.notification_service = NotificationService()
            self.audio_recorder = AudioRecorder(self.config)
            
            # 🔑 ГЛАВНЫЙ СЕРВИС - автовставка
            self.auto_paste_service = AutoPasteService(self.config)
            
            # Async процессор для ускорения
            self.async_processor = AsyncSpeechProcessor(
                self.whisper_service,
                self.punctuation_service
            )
            
            self.logger.info("Все сервисы инициализированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации сервисов: {e}")
            raise
    
    def _create_menu(self):
        """Создание меню"""
        # 🛠 Сохраняем ссылку на пункт записи для правильного доступа
        self.record_menu_item = rumps.MenuItem(
            "🎤 Начать запись", 
            callback=self.toggle_recording
        )
        
        # Пункт меню для выбора метода вставки
        self.paste_method_menu = rumps.MenuItem("📋 Метод вставки")
        self.clipboard_menu_item = rumps.MenuItem(
            "✅ Через буфер обмена",
            callback=self.set_paste_method_clipboard
        )
        self.typing_menu_item = rumps.MenuItem(
            "⬜ Прямой ввод",
            callback=self.set_paste_method_typing
        )

        self.paste_method_menu.add(self.clipboard_menu_item)
        self.paste_method_menu.add(self.typing_menu_item)

        self.menu = [
            rumps.MenuItem("📍 Статус: Готов", callback=None),
            rumps.separator,
            self.record_menu_item,  # Используем сохранённую ссылку
            rumps.separator,
            self.paste_method_menu,  # Меню выбора метода вставки
            rumps.separator,
            rumps.MenuItem("📋 Копировать текст", callback=self.copy_text),
            rumps.MenuItem("📝 Показать текст", callback=self.show_text),
            rumps.separator,
            rumps.MenuItem("ℹ️ О программе", callback=self.show_about),
            rumps.MenuItem("🧹 Очистить память", callback=self.manual_cleanup),
        ]
    
    def _start_hotkeys(self):
        """Запуск горячих клавиш"""
        try:
            # Передаём self (rumps.App), чтобы колбэк шёл в главный поток
            self.hotkey_manager = HotkeyManager(rumps_app_instance=self)
            self.hotkey_manager.set_callback(self._on_hotkey_pressed)
            self.hotkey_manager.start()
            self.logger.info("Горячие клавиши активированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка горячих клавиш: {e}")
    
    def _on_hotkey_pressed(self):
        """Обработка Option+Space"""
        if self.is_processing:
            return

        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def set_paste_method_clipboard(self, _):
        """Установить метод вставки через буфер обмена"""
        self.use_clipboard_paste = True
        self.clipboard_menu_item.title = "✅ Через буфер обмена"
        self.typing_menu_item.title = "⬜ Прямой ввод"
        self.logger.info("📋 Метод вставки: через буфер обмена")

    def set_paste_method_typing(self, _):
        """Установить метод вставки через прямой ввод"""
        self.use_clipboard_paste = False
        self.clipboard_menu_item.title = "⬜ Через буфер обмена"
        self.typing_menu_item.title = "✅ Прямой ввод"
        self.logger.info("⌨️ Метод вставки: прямой ввод символов")
    
    def _update_status(self, status: str):
        """Обновление статуса в меню"""
        if hasattr(self, 'menu') and self.menu:
            self.menu["📍 Статус: Готов"].title = f"📍 Статус: {status}"
    
    def _update_icon(self, recording: bool = False):
        """Обновление иконки"""
        if recording:
            self.title = "🔴"
        else:
            self.title = "🎤"
    
    @rumps.clicked("🎤 Начать запись")
    def toggle_recording(self, _):
        """Переключение записи"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Начало записи"""
        if self.is_recording or self.is_processing:
            return
            
        try:
            self.is_recording = True
            self.recording_start_time = time.time()
            self._update_progress("RECORDING")
            
            # Обновляем меню
            self.record_menu_item.title = "⏹ Остановить запись"
            
            # Уведомление о начале записи
            self.notification_service.notify_recording_started()
            
            # Простая запись
            self.audio_recorder.start_recording()
            
            # Запускаем таймер записи
            self._start_recording_timer()
            
            self.logger.info("Запись начата")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи: {e}")
            self.is_recording = False
            self._update_progress("IDLE")
            self.notification_service.notify_error(str(e))
    
    def stop_recording(self):
        """Остановка записи"""
        if not self.is_recording:
            return
            
        try:
            self.is_recording = False
            self._stop_recording_timer()
            
            # Обновляем прогресс
            self._update_progress("PROCESSING")
            
            # Остановка записи
            audio_data = self.audio_recorder.stop_recording()
            duration = len(audio_data) / 16000 if audio_data is not None else 0
            
            # Уведомление об остановке
            self.notification_service.notify_recording_stopped(duration)
            
            # Обновляем меню
            self.record_menu_item.title = "🎤 Начать запись"
            
            if audio_data is not None and len(audio_data) > 0:
                # Обработка в отдельном потоке
                threading.Thread(
                    target=self._process_audio,
                    args=(audio_data,),
                    daemon=True
                ).start()
            else:
                self.logger.warning("Нет аудио данных для обработки")
                self._update_progress("IDLE")
                
        except Exception as e:
            self.logger.error(f"Ошибка остановки записи: {e}")
            self._update_progress("IDLE")
            self.notification_service.notify_error(str(e))
    
    def _process_audio(self, audio_data):
        """Простая обработка аудио с автовставкой"""
        try:
            self.is_processing = True
            
            # Callback для обновления прогресса
            def progress_callback(stage):
                """Callback для обновления прогресса"""
                stage_map = {
                    "vad": "PROCESSING",
                    "transcription": "TRANSCRIBING", 
                    "punctuation": "PUNCTUATING",
                    "llm": "FINALIZING"
                }
                if stage in stage_map:
                    self._update_progress(stage_map[stage])
            
            # Обработка через async процессор
            result = self.async_processor.process_audio_sync(
                audio_data,
                progress_callback=progress_callback,
            )
            
            # Исправлено: result это tuple (text, llm_summary)
            if result and isinstance(result, tuple) and len(result) >= 2:
                final_text, llm_summary = result
                if final_text and final_text.strip():
                    self._finalize_processing(final_text)
                else:
                    self.logger.warning("Получен пустой результат транскрипции")
                    self._update_progress("IDLE")
            else:
                self.logger.warning("Не удалось получить результат транскрипции")
                self._update_progress("IDLE")
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки аудио: {e}")
            self.notification_service.notify_error(str(e))
            self._update_progress("IDLE")
        finally:
            self.is_processing = False
    
    def _finalize_processing(self, text):
        """Простая финализация с автовставкой"""
        try:
            # Показываем финализацию
            self._update_progress("FINALIZING")
            
            self.is_processing = False
            
            if not text or not text.strip():
                self.notification_service.notify_no_speech()
                self._update_progress("IDLE")
                return
            
            # Сохраняем текст
            final_text = text.strip()
            self.last_text = final_text
            
            # 🎯 ПРОСТАЯ АВТОВСТАВКА
            try:
                auto_paste_enabled = self.config.ui.get("auto_paste_enabled", True)
                
                if auto_paste_enabled:
                    self.logger.info(f"📝 Автовставка текста: {len(final_text)} символов")
                    
                    # Обычная автовставка с выбранным методом
                    success = self.auto_paste_service.paste_text(
                        final_text,
                        use_clipboard=self.use_clipboard_paste
                    )
                    if success:
                        self.logger.info("✅ Автовставка выполнена успешно")
                    else:
                        self.logger.warning("⚠️ Автовставка не удалась")
                else:
                    self.logger.info("Автовставка отключена в настройках")
                    
            except Exception as e:
                self.logger.error(f"Ошибка автовставки: {e}")
            
            # Показываем результат
            self.notification_service.notify_transcription_complete(
                text=self.last_text
            )
                
            # Копируем в буфер обмена
            try:
                pyperclip.copy(self.last_text)
                self.logger.info("Текст скопирован в буфер обмена")
            except Exception as e:
                self.logger.error(f"Ошибка копирования: {e}")
            
            # Принудительная очистка памяти после обработки
            self._cleanup_after_processing()
            
            # Возвращаемся в готовое состояние
            self._update_progress("IDLE")
            
        except Exception as e:
            self.logger.error(f"Ошибка финализации: {e}")
            self.notification_service.notify_error(str(e))
            self._update_progress("IDLE")
    
    def _cleanup_after_processing(self):
        """Очистка памяти после каждой обработки"""
        try:
            # Очищаем буферы сервисов
            if hasattr(self, 'audio_recorder'):
                self.audio_recorder.cleanup()
            
            # Принудительная сборка мусора если включена в настройках
            performance = self.config.performance
            if performance.get("force_garbage_collection", True):
                free_memory("post-processing")
                self.logger.debug("Принудительная очистка памяти выполнена")
            
            # Очищаем async процессор если используется
            if hasattr(self, 'async_processor'):
                self.async_processor._cleanup_memory()
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки после обработки: {e}")

    def manual_cleanup(self, _):
        """Ручная очистка памяти из меню."""
        try:
            self.logger.info("Ручная очистка памяти…")
            if hasattr(self, 'audio_recorder'):
                self.audio_recorder.cleanup()
            if hasattr(self, 'async_processor'):
                self.async_processor._cleanup_memory()
            free_memory("manual")
            log_process_memory("after manual cleanup")
            rumps.alert("Память очищена")
        except Exception as e:
            self.logger.error(f"Ошибка ручной очистки: {e}")
    
    @rumps.clicked("📋 Копировать текст")
    def copy_text(self, _):
        """Копирование последнего текста"""
        if not self.last_text:
            rumps.alert("Нет текста для копирования")
            return
            
        pyperclip.copy(self.last_text)
        self.notification_service.send_notification(
            title="📋 Скопировано",
            message="Текст скопирован в буфер обмена"
        )
    
    @rumps.clicked("📝 Показать текст")
    def show_text(self, _):
        """Показ последнего текста"""
        if not self.last_text:
            rumps.alert("Нет текста для отображения")
            return
        
        display_text = self.last_text
        if len(display_text) > 500:
            display_text = display_text[:500] + "..."
            
        rumps.alert(
            title="Последний текст",
            message=display_text,
            ok="OK"
        )
    
    @rumps.clicked("ℹ️ О программе")
    def show_about(self, _):
        """О программе"""
        rumps.alert(
            title="SuperWhisper Simple",
            message=f"v{self.config.app['version']}\n\n"
                   "🚀 Возможности:\n"
                   "• Быстрая транскрипция\n"
                   "• Автоматическая вставка\n"
                   "• Простота использования\n\n"
                   "⌨️ Option+Space - запись/остановка",
            ok="OK"
        )

    def _start_recording_timer(self):
        """Запуск таймера записи"""
        def update_timer():
            while self.is_recording:
                self._update_progress("RECORDING")
                time.sleep(1)
        
        self.recording_timer = threading.Thread(target=update_timer, daemon=True)
        self.recording_timer.start()
    
    def _stop_recording_timer(self):
        """Остановка таймера записи"""
        if self.recording_timer and self.recording_timer.is_alive():
            # Таймер остановится сам когда is_recording станет False
            pass

    def _update_progress(self, state_key: str, extra_info: str = ""):
        """Обновление прогресса с анимированной иконкой"""
        try:
            icon, description = getattr(ProgressStates, state_key)
            
            # Форматируем описание если нужно
            if "{time}" in description and self.recording_start_time:
                elapsed = time.time() - self.recording_start_time
                time_str = f"{int(elapsed//60):02d}:{int(elapsed%60):02d}"
                description = description.format(time=time_str)
            
            # Обновляем иконку и статус
            self.title = icon
            self._update_status(description + extra_info)
            
            self.logger.info(f"Прогресс: {description}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления прогресса: {e}")


def main():
    """Главная функция"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка на уникальность процесса
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "superwhisper.py"], 
            capture_output=True, 
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            if len(pids) > 1:  # Больше одного процесса
                logger.warning("Приложение уже запущено. Завершение.")
                return
        
        config = Config("config.yaml")
        logger.info("🚀 Запуск SuperWhisper Simple")
        
        app = SuperWhisperSimple(config)
        app.run()
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main() 