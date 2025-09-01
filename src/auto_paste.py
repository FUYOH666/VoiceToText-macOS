"""
Сервис автоматической вставки текста в активное приложение
"""

import logging
import time
import pyperclip
import subprocess
from pynput.keyboard import Key, Controller


class AutoPasteService:
    """Сервис для автоматической вставки текста"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.keyboard = Controller()
        self.config = config
        
        # Настройки из конфига
        self.enabled = True
        self.paste_delay = 0.1  # Задержка перед вставкой
        self.safe_apps = [
            "com.apple.dt.Xcode",
            "com.microsoft.VSCode", 
            "com.apple.TextEdit",
            "com.apple.Notes",
            "com.apple.mail",
            "com.tinyspeck.slackmacgap",
            "com.hnc.Discord",
            "com.apple.Safari",
            "com.google.Chrome"
        ]
        
        if config and hasattr(config, 'ui'):
            self.enabled = config.ui.get('auto_paste_enabled', True)
            self.paste_delay = config.ui.get('auto_paste_delay', 0.1)
            self.force_mode = config.ui.get('auto_paste_force_mode', False)
    
    def paste_text(self, text: str, use_clipboard: bool = True) -> bool:
        """
        Автоматически вставляет текст в активное приложение
        
        Args:
            text: Текст для вставки
            use_clipboard: Использовать буфер обмена для вставки
            
        Returns:
            True если вставка успешна
        """
        try:
            if not self.enabled:
                self.logger.debug("Автовставка отключена")
                return False
            
            if not text or not text.strip():
                self.logger.warning("Пустой текст для вставки")
                return False
            
            # ИСПРАВЛЕНИЕ: Убираем ВСЕ лишние пробелы в начале и конце
            text = text.strip()
            
            # Проверяем безопасность (если не force режим)
            if not getattr(self, 'force_mode', False):
                if not self._is_safe_to_paste():
                    self.logger.warning("Небезопасное приложение для автовставки")
                    self.logger.info("Подсказка: включите auto_paste_force_mode в config.yaml")
                    return False
            else:
                self.logger.info("Force режим: пропускаем проверки безопасности")
            
            self.logger.info(f"🔄 Автовставка текста: {len(text)} символов")
            force_mode = getattr(self, 'force_mode', False)
            self.logger.info(f"📋 Настройки - enabled: {self.enabled}, "
                            f"delay: {self.paste_delay}, force: {force_mode}")
            
            # Короткая задержка
            time.sleep(self.paste_delay)
            
            if use_clipboard:
                # Метод 1: Через буфер обмена (более надежно)
                original_clipboard = self._get_clipboard_safely()
                
                # Копируем наш текст
                pyperclip.copy(text)
                time.sleep(0.05)
                
                # Вставляем через Cmd+V
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                
                # Восстанавливаем оригинальный буфер обмена
                time.sleep(0.1)
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            else:
                # Метод 2: Прямой ввод символов (медленнее)
                self.keyboard.type(text)
            
            self.logger.info("Автовставка завершена успешно")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка автовставки: {e}")
            return False
    
    def _get_clipboard_safely(self) -> str:
        """Безопасно получает содержимое буфера обмена"""
        try:
            return pyperclip.paste()
        except Exception:
            return ""
    
    def _is_safe_to_paste(self) -> bool:
        """
        🎯 НОВАЯ ФУНКЦИЯ - РАЗРЕШАЕМ АВТОВСТАВКУ ВЕЗДЕ!
        
        Returns:
            Всегда True - убираем все ограничения!
        """
        try:
            # Всё равно логируем приложение для информации
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            try:
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if result.returncode == 0:
                    app_name = result.stdout.strip()
                    self.logger.info(f"Активное приложение: '{app_name}'")
                    self.logger.info(f"🎯 Приложение '{app_name}' - АВТОВСТАВКА РАЗРЕШЕНА")
                    
            except Exception as script_error:
                self.logger.debug(f"Не удалось определить приложение: {script_error}")
            
            # 🎯 ВСЕГДА ВОЗВРАЩАЕМ TRUE - убираем все ограничения!
            return True
            
        except Exception as e:
            self.logger.debug(f"Ошибка проверки приложения: {e}")
            # 🎯 ДАЖЕ ПРИ ОШИБКЕ РАЗРЕШАЕМ!
            return True
    
    def quick_paste(self, text: str) -> bool:
        """
        Быстрая вставка без проверок (для экстренных случаев)
        
        Args:
            text: Текст для вставки
            
        Returns:
            True если успешно
        """
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press('v')
                self.keyboard.release('v')
            
            return True
        except Exception as e:
            self.logger.error(f"Ошибка быстрой вставки: {e}")
            return False 

    def _is_safe_application(self, app_name: str) -> bool:
        """
        🆕 Проверяет безопасность приложения для автовставки
        Теперь РАЗРЕШАЕМ ВЕЗДЕ!
        """
        try:
            if not app_name:
                return False
            
            # 🎯 УБИРАЕМ ВСЕ ОГРАНИЧЕНИЯ - разрешаем везде!
            self.logger.info(f"Приложение '{app_name}' безопасно для автовставки")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки безопасности: {e}")
            return False 