import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from app.config import settings
from .base import BaseAIProvider

GITHUB_ENDPOINT = "https://models.github.ai/inference"
MODEL_NAME = "openai/gpt-4o-mini"


class APIProvider(BaseAIProvider):

    def __init__(self):
        self.client = OpenAI(
            base_url=GITHUB_ENDPOINT,
            api_key=settings.github_token,
        )
        self.model = MODEL_NAME

    def _call(self, system: str, user: str, max_tokens: int = 2000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "developer", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def _parse_json(self, text: str) -> Any:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)

    async def generate_questions(
        self, topic, content, difficulty_levels, count=5, language="ru"
    ) -> List[Dict[str, Any]]:
        system = "You are an educational content creator. Always respond with valid JSON only."
        user = f"""Создай {count} вопросов с множественным выбором по теме "{topic}".
Уровни сложности: {", ".join(difficulty_levels)}.
Создай вопросы для КАЖДОГО уровня (по {count} на каждый).

Материал:
{content[:3000]}

Ответь ТОЛЬКО JSON:
```json
{{
  "questions": [
    {{
      "level": "easy|medium|hard",
      "question": "...",
      "answers": [
        {{"text": "...", "correct": true}},
        {{"text": "...", "correct": false}},
        {{"text": "...", "correct": false}},
        {{"text": "...", "correct": false}}
      ],
      "explanation": "..."
    }}
  ]
}}
```
Язык ответа: {language}"""

        text = self._call(system, user, max_tokens=2000)
        data = self._parse_json(text)
        return data["questions"]

    async def generate_cases(
        self, topic, content, case_type, count=2, language="ru"
    ) -> List[Dict[str, Any]]:
        system = "You are an educational content creator. Always respond with valid JSON only."

        if case_type == "battle":
            user = f"""Создай {count} противоположных кейса для дискуссии по теме "{topic}".

Материал:
{content[:3000]}

Ответь ТОЛЬКО JSON:
```json
{{
  "cases": [
    {{"side": "A", "title": "...", "description": "...", "key_arguments": ["...", "..."]}},
    {{"side": "B", "title": "...", "description": "...", "key_arguments": ["...", "..."]}}
  ]
}}
```
Язык: {language}"""
        else:
            user = f"""Создай кейс для анализа по теме "{topic}".
Кейс должен содержать ошибку или проблему для разбора студентами.

Материал:
{content[:3000]}

Ответь ТОЛЬКО JSON:
```json
{{
  "cases": [
    {{
      "title": "...",
      "description": "...",
      "question": "Найдите ошибку и объясните...",
      "correct_answer": "..."
    }}
  ]
}}
```
Язык: {language}"""

        text = self._call(system, user, max_tokens=1500)
        data = self._parse_json(text)
        return data["cases"]

    async def generate_flashcards(
        self, content, count=10, language="ru"
    ) -> List[Dict[str, str]]:
        system = "You are an educational content creator. Always respond with valid JSON only."
        user = f"""Извлеки {count} ключевых терминов и создай карточки из материала.

Материал:
{content[:3000]}

Ответь ТОЛЬКО JSON:
```json
{{
  "cards": [
    {{"term": "...", "definition": "..."}}
  ]
}}
```
Язык: {language}"""

        text = self._call(system, user, max_tokens=1500)
        data = self._parse_json(text)
        return data["cards"]

    async def generate_reference_retelling(
        self, content, topic, language="ru"
    ) -> str:
        system = "You are an educational assistant."
        user = f"""Создай эталонный краткий пересказ материала по теме "{topic}".
Пересказ должен быть 100-150 слов, включать ключевые идеи.

Материал:
{content[:3000]}

Язык: {language}"""

        return self._call(system, user, max_tokens=500)

    async def analyze_content(self, content, language="ru") -> Dict[str, Any]:
        system = "You are an educational content analyzer. Always respond with valid JSON only."
        user = f"""Проанализируй учебный материал и создай кластер знаний.

Материал:
{content[:3000]}

Ответь ТОЛЬКО JSON:
```json
{{
  "main_topic": "...",
  "subtopics": ["...", "..."],
  "key_concepts": ["...", "..."],
  "difficulty_estimate": "beginner|intermediate|advanced",
  "suggested_question_count": 10
}}
```
Язык: {language}"""

        text = self._call(system, user, max_tokens=800)
        return self._parse_json(text)

    async def health_check(self) -> bool:
        try:
            self._call("You are a helpful assistant.", "ping", max_tokens=5)
            return True
        except Exception:
            return False
