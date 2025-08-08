"""
Сервис нативных уведомлений для macOS
"""

import logging
import subprocess
from typing import Optional


class NotificationService:
    """Сервис для отправки нативных уведомлений macOS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_name = "SuperWhisper"
    
    def send_notification(
        self, 
        title: str, 
        message: str, 
        subtitle: Optional[str] = None,
        sound: bool = False
    ):
        """
        Отправляет нативное уведомление macOS
        
        Args:
            title: Заголовок уведомления
            message: Текст уведомления
            subtitle: Подзаголовок (опционально)
            sound: Воспроизводить звук
        """
        try:
            # Команда для osascript (AppleScript)
            script_parts = [
                'osascript',
                '-e',
                f'display notification "{message}"'
            ]
            
            # Добавляем заголовок
            script_parts[2] += f' with title "{title}"'
            
            # Добавляем подзаголовок если есть
            if subtitle:
                script_parts[2] += f' subtitle "{subtitle}"'
            
            # Добавляем звук
            if sound:
                script_parts[2] += ' sound name "Glass"'
            
            # Выполняем команду
            subprocess.run(script_parts, check=True, capture_output=True)
            self.logger.debug(f"Уведомление отправлено: {title} - {message}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка уведомления: {e}")
    
    def notify_recording_started(self):
        """Уведомление о начале записи"""
        self.send_notification(
            title="🎤 Запись начата",
            message="Говорите, SuperWhisper слушает...",
            sound=True
        )
    
    def notify_recording_stopped(self, duration: float):
        """Уведомление об остановке записи"""
        self.send_notification(
            title="⏹ Запись остановлена",
            message=f"Длительность: {duration:.1f} сек. Обрабатываем...",
            sound=False
        )
    
    def notify_processing_stage(self, stage: str):
        """Уведомление о стадии обработки"""
        self.send_notification(
            title="⚡ Обработка",
            message=stage,
            sound=False
        )
    
    def notify_text_ready(self, text_length: int, pasted: bool = None):
        """Уведомление о готовности текста"""
        if pasted is True:
            message = (f"Текст распознан ({text_length} символов) "
                       "и автоматически вставлен")
            title = "✅ Готово и вставлено"
        elif pasted is False:
            message = (f"Текст распознан ({text_length} символов) "
                       "и скопирован в буфер")
            title = "✅ Готово"
        else:
            message = f"Текст распознан ({text_length} символов) и скопирован"
            title = "✅ Готово"
            
        self.send_notification(
            title=title,
            message=message,
            sound=True
        )
    
    def notify_no_speech(self):
        """Уведомление об отсутствии речи"""
        self.send_notification(
            title="🤫 Тишина",
            message="Речь не обнаружена",
            sound=False
        )
    
    def notify_transcription_complete(self, text: str):
        """Уведомление о завершении транскрипции"""
        preview = text[:50] + "..." if len(text) > 50 else text
        self.send_notification(
            title="✅ Транскрипция готова",
            message=f"Распознано: {preview}",
            sound=True
        )
    

    
    def notify_error(self, error_message: str):
        """Уведомление об ошибке"""
        self.send_notification(
            title="❌ Ошибка",
            message=error_message,
            sound=True
        ) 