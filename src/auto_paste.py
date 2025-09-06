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
        self.force_mode = False  # По умолчанию не в force режиме
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

        # ОТЛАДКА: Логируем настройки при инициализации
        self.logger.info(f"🔧 AutoPasteService инициализирован:")
        self.logger.info(f"   - enabled: {self.enabled}")
        self.logger.info(f"   - delay: {self.paste_delay}")
        self.logger.info(f"   - force_mode: {self.force_mode}")
        self.logger.info(f"   - safe_apps: {len(getattr(self, 'safe_apps', []))} приложений")
    
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
            # Убираем лишние пробелы СРАЗУ
            text = text.strip()
            
            self.logger.info(f"🔄 Автовставка: '{text[:50]}...' ({len(text)} симв.)")

            if not self.enabled:
                self.logger.debug("Автовставка отключена в настройках")
                return False

            if not text:
                self.logger.warning("Пустой текст для вставки")
                return False
            
            # 🆕 ПРИНУДИТЕЛЬНЫЙ РЕЖИМ - пробуем всегда вставить
            active_app = self._get_active_app_name()
            self.logger.info(f"🎯 Активное приложение: {active_app}")
            
            # Проверяем безопасность только если НЕ force режим
            force_mode = getattr(self, 'force_mode', False)
            if not force_mode and not self._is_safe_to_paste():
                self.logger.warning("⚠️ Небезопасное приложение для автовставки")
                self.logger.info("💡 Включите auto_paste_force_mode в config.yaml для принудительной вставки")
                # 🆕 НО ПОПРОБУЕМ ВСТАВИТЬ ЧЕРЕЗ БУФЕР ОБМЕНА
                self.logger.info("🔄 Пробуем через буфер обмена...")
                use_clipboard = True
            else:
                self.logger.info("✅ Безопасное приложение или force режим")

            # Короткая задержка перед вставкой
            time.sleep(self.paste_delay)
            
            if use_clipboard:
                # Метод 1: Через буфер обмена (более надежно)
                self.logger.info("📋 Начинаем вставку через буфер обмена")

                # Сохраняем оригинальный буфер
                original_clipboard = self._get_clipboard_safely()
                self.logger.info(f"💾 Оригинальный буфер: '{original_clipboard[:50]}...'")

                # Копируем наш текст
                pyperclip.copy(text)
                time.sleep(0.05)

                # Проверяем что текст скопировался
                copied_text = self._get_clipboard_safely()
                self.logger.info(f"📝 Скопированный текст: '{copied_text}'")

                if copied_text != text:
                    self.logger.warning(f"❌ Текст не скопировался правильно! Ожидалось: '{text}', получено: '{copied_text}'")

                # 🆕 УЛУЧШЕННАЯ ВСТАВКА - пробуем несколько раз
                self.logger.info("⌨️ Отправляем Cmd+V")
                
                for attempt in range(3):  # 3 попытки
                    try:
                        with self.keyboard.pressed(Key.cmd):
                            self.keyboard.press('v')
                            self.keyboard.release('v')
                        
                        # Ждем завершения вставки
                        time.sleep(0.2)  # Увеличиваем задержку
                        
                        self.logger.info(f"✅ Попытка {attempt + 1}: Cmd+V отправлен")
                        break
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Попытка {attempt + 1} не удалась: {e}")
                        if attempt == 2:  # Последняя попытка
                            raise
                        time.sleep(0.1)

                # Восстанавливаем оригинальный буфер обмена
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
                    self.logger.info("🔄 Буфер обмена восстановлен")
            else:
                # Метод 2: Прямой ввод символов (медленнее)
                self.logger.info("⌨️ Используем прямой ввод символов")
                self.keyboard.type(text)
            
            self.logger.info("✅ Автовставка завершена успешно")
            return True

        except Exception as e:
            self.logger.error(f"❌ Ошибка автовставки: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _get_clipboard_safely(self) -> str:
        """Безопасно получает содержимое буфера обмена"""
        try:
            return pyperclip.paste()
        except Exception:
            return ""
    
    def _is_safe_to_paste(self) -> bool:
        """
        🎯 УПРОЩЕННАЯ ПРОВЕРКА БЕЗОПАСНОСТИ
        
        Returns:
            True если приложение безопасно для вставки
        """
        try:
            # 🆕 ПРОСТАЯ ЛОГИКА - РАЗРЕШАЕМ ВСТАВКУ ВЕЗДЕ
            app_name = self._get_active_app_name()
            self.logger.info(f"🎯 Активное приложение: '{app_name}' - АВТОВСТАВКА РАЗРЕШЕНА")
            
            # Всегда возвращаем True - убираем все ограничения!
            return True
            
        except Exception as e:
            self.logger.debug(f"Не удалось определить приложение: {e}")
            # Всё равно разрешаем вставку
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

    def _get_active_app_name(self) -> str:
        """
        Определяет название активного приложения

        Returns:
            Название активного приложения
        """
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "unknown"

        except Exception as e:
            self.logger.debug(f"Не удалось определить активное приложение: {e}")
            return "unknown" 