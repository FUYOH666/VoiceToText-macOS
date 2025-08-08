"""
Менеджер глобальных горячих клавиш для SuperWhisper
"""

import logging
from typing import Callable, Optional
import rumps
from pynput import keyboard
from pynput.keyboard import Key


class HotkeyManager:
    """Менеджер для обработки глобальных горячих клавиш"""

    def __init__(self, rumps_app_instance: Optional[object] = None):
        """Инициализация менеджера горячих клавиш"""
        self.logger = logging.getLogger(__name__)
        self.listener = None
        self.callback: Optional[Callable] = None
        self.is_running = False

        # Состояние клавиш для комбинации Option + Space
        self.pressed_keys = set()
        # Ссылка на экземпляр rumps.App (для ясности; не обязательна)
        self.rumps_app_instance = rumps_app_instance
        # Option = Alt на Mac (для pynput)
        self.target_keys = {Key.alt_l, Key.alt_r, Key.space}

    def set_callback(self, callback: Callable):
        """
        Устанавливает callback функцию для обработки горячих клавиш

        Args:
            callback: Функция которая будет вызвана при нажатии горячих клавиш
        """
        self.callback = callback

    def start(self):
        """Запускает прослушивание глобальных горячих клавиш"""
        try:
            if self.is_running:
                return

            self.logger.info(
                "Запуск прослушивания глобальных горячих клавиш (Option+Space)"
            )

            # Создаем listener в отдельном потоке
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )

            self.is_running = True
            self.listener.start()

            self.logger.info("Прослушивание горячих клавиш активно")

        except Exception as e:
            self.logger.error(f"Ошибка запуска прослушивания клавиш: {e}")
            self.is_running = False

    def stop(self):
        """Останавливает прослушивание горячих клавиш"""
        try:
            if not self.is_running:
                return

            self.is_running = False

            if self.listener:
                self.listener.stop()
                self.listener = None

            self.logger.info("Прослушивание горячих клавиш остановлено")

        except Exception as e:
            self.logger.error(f"Ошибка остановки прослушивания клавиш: {e}")

    def _on_key_press(self, key):
        """
        Обработчик нажатия клавиш

        Args:
            key: Нажатая клавиша
        """
        try:
            # Добавляем клавишу в набор нажатых
            self.pressed_keys.add(key)

            # Проверяем комбинацию Option + Space
            if self._is_hotkey_combination():
                self.logger.info("Обнаружена комбинация Option+Space")
                if self.callback and self.rumps_app_instance is not None:
                    # Выполняем callback в основном потоке через rumps.Timer
                    def _run_on_main_thread(_):
                        try:
                            if self.callback:
                                self.callback()
                        finally:
                            # Останавливаем таймер после одного срабатывания
                            timer.stop()

                    timer = rumps.Timer(_run_on_main_thread, 0.001)
                    timer.start()
                elif self.callback:
                    # Фолбэк: запуск напрямую (может тронуть UI не из главного
                    # потока)
                    self.logger.warning(
                        "rumps_app_instance не передан в HotkeyManager"
                    )
                    self.logger.warning(
                        "Callback может выполняться не в главном потоке"
                    )
                    self.callback()

        except Exception as e:
            self.logger.error(f"Ошибка обработки нажатия клавиши: {e}")

    def _on_key_release(self, key):
        """
        Обработчик отпускания клавиш

        Args:
            key: Отпущенная клавиша
        """
        try:
            # Удаляем клавишу из набора нажатых
            self.pressed_keys.discard(key)

        except Exception as e:
            self.logger.error(f"Ошибка обработки отпускания клавиши: {e}")

    def _is_hotkey_combination(self) -> bool:
        """
        Проверяет нажата ли комбинация Option + Space

        Returns:
            True если нажата нужная комбинация
        """
        try:
            # Проверяем есть ли Alt (Option) и Space среди нажатых клавиш
            alt_keys = [Key.alt_l, Key.alt_r]
            has_alt = any(key in self.pressed_keys for key in alt_keys)
            has_space = Key.space in self.pressed_keys

            return has_alt and has_space

        except Exception as e:
            self.logger.error(f"Ошибка проверки комбинации клавиш: {e}")
            return False

    def __del__(self):
        """Деструктор - останавливает прослушивание"""
        try:
            if hasattr(self, 'is_running') and self.is_running:
                self.stop()
        except Exception:
            # Игнорируем ошибки в деструкторе
            pass
