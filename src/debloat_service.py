"""
Сервис де-болтовни для SuperWhisper
Вычищает междометия, повторы и разговорные конструкции
"""

import logging
import re
from typing import Dict, List, Set


class DebloatService:
    """Сервис для очистки текста от разговорных конструкций"""

    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Настройки
        self.enabled = True
        self.aggressive_mode = False  # Для сильной очистки
        self.quiet_mode = True  # Тихий режим без логов

        if config and hasattr(config, 'debloat'):
            debloat_config = config.debloat
            self.enabled = debloat_config.get('enabled', True)
            self.aggressive_mode = debloat_config.get('aggressive_mode', False)

        # Междометия и разговорные конструкции
        self.filler_words = {
            # Базовые междометия
            'ну', 'вот', 'типа', 'как бы', 'в общем', 'в общем-то',
            'так сказать', 'понимаешь', 'знаешь', 'слушай', 'смотри',
            'короче', 'в смысле', 'вот так', 'вот это', 'вот оно',
            'вот что', 'вот как', 'вот почему', 'вот зачем',

            # Указательные конструкции
            'вон тот', 'вон та', 'вон то', 'вон те',
            'вот тот', 'вот та', 'вот то', 'вот те',
            'там тот', 'там та', 'там то', 'там те',

            # Разговорные усилители
            'очень-очень', 'просто-просто', 'совсем-совсем',
            'абсолютно', 'полностью', 'совершенно',

            # Паразитические слова
            'э-э', 'э-э-э', 'ммм', 'гмм', 'эээ', 'а-а', 'а-а-а',

            # Дополнительные разговорные конструкции
            'в принципе', 'в целом', 'в итоге', 'в конце концов',
            'в любом случае', 'в любом', 'в общем', 'в основном',
            'в частности', 'в частности', 'в связи', 'в связи с',
            'в том числе', 'в то время', 'в то же время',
            'в первую очередь', 'в последнюю очередь',

            # Междометия типа "эээ", "ммм" в разных вариациях
            'э', 'э-э', 'э-э-э', 'э-э-э-э', 'э-э-э-э-э',
            'мм', 'ммм', 'мммм', 'ммммм',
            'а', 'а-а', 'а-а-а', 'а-а-а-а',
            'гм', 'гмм', 'гммм',

            # Разговорные вводные слова
            'значит', 'итак', 'стало быть', 'следовательно',
            'таким образом', 'иными словами', 'другими словами',
            'попросту говоря', 'простыми словами',

            # Фразы-паразиты
            'ну вот', 'ну что', 'ну как', 'ну да', 'ну нет',
            'вот видишь', 'вот смотри', 'вот слушай',
            'знаешь ли', 'понимаешь ли', 'видишь ли'
        }

        # Фразы для замены
        self.phrase_replacements = {
            # Удаление междометий
            r'\bну\b': '',
            r'\bвот\b': '',
            r'\bтипа\b': '',
            r'\bкак бы\b': '',
            r'\bв общем\b': '',
            r'\bв общем-то\b': '',
            r'\bтак сказать\b': '',
            r'\bпонимаешь\b': '',
            r'\bзнаешь\b': '',
            r'\bкороче говоря\b': 'проще сказать',
            r'\bкороче\b': '',
            r'\bв смысле\b': '',
            r'\bвот так\b': '',
            r'\bвот это\b': '',
            r'\bвот оно\b': '',
            r'\bвот что\b': '',
            r'\bвот как\b': '',
            r'\bвот почему\b': '',
            r'\bвот зачем\b': '',

            # Замены разговорных конструкций
            r'\bв принципе\b': '',
            r'\bв целом\b': '',
            r'\bв итоге\b': '',
            r'\bв конце концов\b': 'в итоге',
            r'\bв любом случае\b': 'все равно',
            r'\bв общем\b': '',
            r'\bв основном\b': '',
            r'\bв частности\b': '',

            # Улучшение формулировок
            r'\bзначит\b': '',
            r'\bитак\b': '',
            r'\bстало быть\b': '',
            r'\bтаким образом\b': '',
            r'\bиными словами\b': 'проще говоря',
            r'\bдругими словами\b': 'иными словами',
            r'\bпопросту говоря\b': 'проще говоря',
            r'\bпростыми словами\b': 'проще говоря',

            # Специальные замены для терминов разработки
            r'\bгид игнор\b': '.gitignore',
            r'\bкит игнор\b': '.gitignore',
            r'\bgit ignore\b': '.gitignore',
            r'\bredmi\b': 'README.md',
            r'\bридми\b': 'README.md',
            r'\bпитон\b': 'Python',
            r'\bджава\b': 'Java',
            r'\bджс\b': 'JavaScript',
            r'\bджаваскрипт\b': 'JavaScript'
        }

        # Эхо-повторы (одинаковые слова подряд)
        self.echo_pattern = r'\b(\w+)\s+\1\b'

        # Компиляция паттернов для производительности
        self._compile_patterns()

        self.logger.info(f"🧹 DebloatService инициализирован: {len(self.filler_words)} слов для фильтрации")

    def _compile_patterns(self):
        """Компиляция регулярных выражений для производительности"""
        self.compiled_patterns = {}

        # Паттерн для междометий
        filler_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in self.filler_words) + r')\b'
        self.compiled_patterns['fillers'] = re.compile(filler_pattern, re.IGNORECASE)

        # Паттерн для эхо-повторов
        self.compiled_patterns['echo'] = re.compile(self.echo_pattern, re.IGNORECASE)

    def process_text(self, text: str) -> str:
        """Обрабатывает текст, удаляя разговорные конструкции"""
        if not self.enabled or not text:
            return text

        try:
            original_length = len(text)

            # Шаг 1: Удаление междометий
            text = self._remove_fillers(text)

            # Шаг 2: Удаление эхо-повторов
            text = self._remove_echo_repeats(text)

            # Шаг 3: Очистка лишних пробелов и знаков препинания
            text = self._cleanup_formatting(text)

            # Шаг 4: Агрессивная очистка (опционально)
            if self.aggressive_mode:
                text = self._aggressive_cleanup(text)

            final_length = len(text)
            removed_chars = original_length - final_length

            if removed_chars > 0 and not self.quiet_mode:
                self.logger.debug(f"🧹 Де-болтовня: удалено {removed_chars} символов")

            return text

        except Exception as e:
            self.logger.error(f"Ошибка де-болтовни: {e}")
            return text

    def _remove_fillers(self, text: str) -> str:
        """Удаляет междометия и разговорные конструкции"""
        try:
            # СНАЧАЛА обрабатываем фразы (чтобы "короче говоря" не стало "говоря")
            for pattern, replacement in self.phrase_replacements.items():
                if replacement:  # Только для фраз с заменой, не для удаления
                    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            # ПОТОМ удаляем одиночные междометия
            text = self.compiled_patterns['fillers'].sub('', text)

            # И фразы для удаления (без замены)
            for pattern, replacement in self.phrase_replacements.items():
                if not replacement:  # Только для удаления
                    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка удаления междометий: {e}")
            return text

    def _remove_echo_repeats(self, text: str) -> str:
        """Удаляет эхо-повторы слов"""
        try:
            # Находим и удаляем повторяющиеся слова
            text = self.compiled_patterns['echo'].sub(r'\1', text)

            # Также обрабатываем более сложные повторы типа "слово слово слово"
            words = text.split()
            if len(words) >= 3:
                cleaned_words = []
                i = 0
                while i < len(words):
                    current_word = words[i].lower()

                    # Проверяем, не является ли это повтором
                    if (i + 1 < len(words) and words[i + 1].lower() == current_word and
                        i + 2 < len(words) and words[i + 2].lower() == current_word):
                        # Три одинаковых слова подряд - оставляем только одно
                        cleaned_words.append(words[i])
                        i += 3
                    elif (i + 1 < len(words) and words[i + 1].lower() == current_word):
                        # Два одинаковых слова - оставляем только одно
                        cleaned_words.append(words[i])
                        i += 2
                    else:
                        cleaned_words.append(words[i])
                        i += 1

                text = ' '.join(cleaned_words)

            return text

        except Exception as e:
            self.logger.error(f"Ошибка удаления повторов: {e}")
            return text

    def _cleanup_formatting(self, text: str) -> str:
        """Очищает форматирование после удаления слов"""
        try:
            # Убираем лишние пробелы
            text = re.sub(r'\s+', ' ', text)

            # Убираем пробелы перед знаками препинания
            text = re.sub(r'\s+([.!?,:;])', r'\1', text)

            # Убираем пробелы после открывающих скобок
            text = re.sub(r'([(])\s+', r'\1', text)

            # Добавляем пробелы после закрывающих скобок (если следующий символ - буква)
            text = re.sub(r'([)])\s*([а-яёa-z])', r'\1 \2', text, flags=re.IGNORECASE)

            # Очищаем пробелы в начале и конце
            text = text.strip()

            # Убираем пробелы перед и после кавычек
            text = re.sub(r'\s*"\s*([^"]*)\s*"\s*', r'"\1"', text)
            text = re.sub(r"\s*'\s*([^']*)\s*'\s*", r"'\1'", text)

            # Исправляем множественные знаки препинания
            text = re.sub(r'([.!?])\1+', r'\1', text)  # !!! -> !
            text = re.sub(r',,+', ',', text)  # ,, -> ,

            # Убираем пробелы перед % и после цифр
            text = re.sub(r'(\d)\s*%', r'\1%', text)

            # Очищаем пробелы вокруг тире
            text = re.sub(r'\s*-\s*', '–', text)  # Заменяем дефис на тире

            # Исправляем пробелы вокруг тире
            text = re.sub(r'\s*–\s*', ' – ', text)

            # Убираем пробелы в начале предложений после знаков препинания
            text = re.sub(r'([.!?])\s*([а-яёa-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(),
                         text, flags=re.IGNORECASE)

            # Финальная очистка лишних пробелов
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()

            return text

        except Exception as e:
            self.logger.error(f"Ошибка очистки форматирования: {e}")
            return text

    def _aggressive_cleanup(self, text: str) -> str:
        """Агрессивная очистка для максимальной чистоты текста"""
        try:
            # Удаляем очень короткие слова (1-2 буквы), кроме предлогов
            short_words_to_keep = {'в', 'с', 'к', 'о', 'у', 'а', 'и', 'я', 'ты', 'он', 'мы', 'вы', 'то', 'не', 'да', 'но', 'ли', 'же', 'бы', 'ни', 'во', 'со', 'ко', 'до', 'по', 'об', 'от', 'из', 'на'}

            words = text.split()
            filtered_words = []

            for word in words:
                word_lower = word.lower()
                # Оставляем слова длиннее 2 символов или важные короткие слова
                if len(word) > 2 or word_lower in short_words_to_keep:
                    filtered_words.append(word)

            return ' '.join(filtered_words)

        except Exception as e:
            self.logger.error(f"Ошибка агрессивной очистки: {e}")
            return text

    def add_filler_word(self, word: str):
        """Добавляет новое слово в список междометий"""
        try:
            self.filler_words.add(word.lower())
            self._compile_patterns()  # Перекомпилируем паттерны
            self.logger.info(f"Добавлено междометие: {word}")
        except Exception as e:
            self.logger.error(f"Ошибка добавления междометия: {e}")

    def remove_filler_word(self, word: str):
        """Удаляет слово из списка междометий"""
        try:
            self.filler_words.discard(word.lower())
            self._compile_patterns()  # Перекомпилируем паттерны
            self.logger.info(f"Удалено междометие: {word}")
        except Exception as e:
            self.logger.error(f"Ошибка удаления междометия: {e}")

    def get_stats(self) -> Dict:
        """Возвращает статистику сервиса"""
        return {
            "enabled": self.enabled,
            "aggressive_mode": self.aggressive_mode,
            "filler_words_count": len(self.filler_words),
            "echo_pattern": self.echo_pattern
        }
