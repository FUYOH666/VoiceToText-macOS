"""
Сервис для работы с LLM через LM Studio API
"""

import logging
import requests
import json
from typing import Dict, Any, Optional
from pathlib import Path


class LLMService:
    """Сервис для получения резюме текста через LM Studio"""
    
    def __init__(self, config: Any):
        """
        Инициализация LLM сервиса
        
        Args:
            config: Объект конфигурации
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.endpoint = config.llm["endpoint"]
        self.model = config.llm["model"]
        self.timeout = config.llm["timeout"]
        self.max_tokens = config.llm["max_tokens"]
        self.temperature = config.llm["temperature"]
        
        # Проверяем доступность сервиса
        self._check_service()
    
    def _check_service(self):
        """Проверяет доступность LM Studio API"""
        try:
            response = requests.get(
                f"{self.endpoint}/v1/models",
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info("LM Studio API доступен")
            else:
                self.logger.warning(
                    f"LM Studio API недоступен: {response.status_code}"
                )
                
        except Exception as e:
            self.logger.warning(f"Не удается подключиться к LM Studio: {e}")
    
    def generate_summary(self, text: str, max_length: int = 3) -> Optional[str]:
        """
        Генерирует краткое резюме текста
        
        Args:
            text: Исходный текст для резюме
            max_length: Максимальная длина резюме в предложениях
            
        Returns:
            Краткое резюме или None при ошибке
        """
        try:
            if not text.strip():
                return None
            
            self.logger.info(f"Создание резюме для текста длиной "
                           f"{len(text)} символов")
            
            # Формируем промпт для резюме
            prompt = self._create_summary_prompt(text, max_length)
            
            # Отправляем запрос к LM Studio
            response = self._make_request(prompt)
            
            if response:
                summary = self._extract_summary(response)
                self.logger.info(f"Резюме создано: {summary[:100]}...")
                return summary
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания резюме: {e}")
            return None
    
    def _create_summary_prompt(self, text: str, max_length: int) -> str:
        """
        Создает промпт для генерации резюме
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина резюме
            
        Returns:
            Сформированный промпт
        """
        prompt = f"""Создай краткое резюме следующего текста. 
Резюме должно быть на русском языке и содержать не более {max_length} предложений.
Выдели основные идеи и ключевые моменты.

Текст:
{text}

Краткое резюме:"""
        
        return prompt
    
    def _make_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Отправляет запрос к LM Studio API
        
        Args:
            prompt: Промпт для LLM
            
        Returns:
            Ответ от API или None при ошибке
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(
                    f"Ошибка API: {response.status_code} - {response.text}"
                )
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("Таймаут запроса к LM Studio")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка запроса к LM Studio: {e}")
            return None
    
    def _extract_summary(self, response: Dict[str, Any]) -> str:
        """
        Извлекает резюме из ответа API
        
        Args:
            response: Ответ от LM Studio API
            
        Returns:
            Извлеченное резюме
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                return ""
            
            message = choices[0].get("message", {})
            content = message.get("content", "").strip()
            
            # Очищаем резюме от лишних фраз
            summary = self._clean_summary(content)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения резюме: {e}")
            return ""
    
    def _clean_summary(self, summary: str) -> str:
        """
        Очищает резюме от служебных фраз
        
        Args:
            summary: Исходное резюме
            
        Returns:
            Очищенное резюме
        """
        # Удаляем служебные фразы
        clean_phrases = [
            "краткое резюме:",
            "резюме:",
            "основные моменты:",
            "ключевые идеи:",
            "в тексте говорится о том, что",
            "автор рассказывает о",
        ]
        
        result = summary.lower()
        for phrase in clean_phrases:
            result = result.replace(phrase, "")
        
        # Восстанавливаем регистр первой буквы
        result = result.strip()
        if result:
            result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
        
        return result
    
    def analyze_speakers(self, text: str) -> Optional[str]:
        """
        Анализирует количество говорящих в тексте
        
        Args:
            text: Исходный текст
            
        Returns:
            Информация о говорящих или None
        """
        try:
            if not text.strip():
                return None
            
            prompt = f"""Проанализируй следующий текст и определи:
1. Сколько разных людей говорит в тексте
2. О чем они говорят
3. Есть ли диалог или это монолог

Текст:
{text}

Анализ:"""
            
            response = self._make_request(prompt)
            
            if response:
                return self._extract_summary(response)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа говорящих: {e}")
            return None
    
    def format_text(self, text: str) -> Optional[str]:
        """
        Форматирует текст для лучшей читаемости
        
        Args:
            text: Исходный текст
            
        Returns:
            Отформатированный текст или None
        """
        try:
            if not text.strip():
                return None
            
            prompt = f"""Отформатируй следующий текст для лучшей читаемости:
1. Разбей на абзацы по смыслу
2. Исправь очевидные ошибки
3. Сохрани весь смысл и содержание

Исходный текст:
{text}

Отформатированный текст:"""
            
            response = self._make_request(prompt)
            
            if response:
                return self._extract_summary(response)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования текста: {e}")
            return None 