import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from app.config import settings
from app.services.cache import get_cached, set_cached
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
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
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
        self, topic, content, difficulty_levels, count=5, language="ru", exclude_questions=[]
    ) -> List[Dict[str, Any]]:
        if not exclude_questions:
            cached = await get_cached("questions", topic=topic, content=content[:500], count=count, language=language)
            if cached:
                return cached

        system = "You are an educational content creator. Always respond with valid JSON only."
        if exclude_questions:
            system += (
                " CRITICAL RULE: You MUST NOT repeat, rephrase, or create questions similar"
                " to the FORBIDDEN list provided by the user. Generate entirely new questions"
                " that test different facts, concepts, or aspects of the material."
            )

        exclude_note = ""
        if exclude_questions:
            lines = "\n".join(f"- {q}" for q in exclude_questions[:80])
            exclude_note = f"""

⛔ ЗАПРЕЩЁННЫЕ ВОПРОСЫ (уже использовались — не повторять, не перефразировать):
{lines}

Сгенерируй ТОЛЬКО новые вопросы, проверяющие другие факты и аспекты темы."""

        user = f"""Создай ровно {count} вопросов с множественным выбором по теме "{topic}".
Распредели по уровням сложности: {", ".join(difficulty_levels)}.

Материал:
{content[:3000]}
{exclude_note}

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

        max_tok = min(500 + count * 200, 4000)
        text = self._call(system, user, max_tokens=max_tok)
        data = self._parse_json(text)
        result = data["questions"]
        if not exclude_questions:
            await set_cached("questions", result, topic=topic, content=content[:500], count=count, language=language)
        return result

    async def generate_cases(
        self, topic, content, case_type, count=2, language="ru", exclude_cases=[]
    ) -> List[Dict[str, Any]]:
        if not exclude_cases:
            cached = await get_cached("cases", topic=topic, content=content[:500], case_type=case_type, language=language)
            if cached:
                return cached

        system = "You are an educational content creator. Always respond with valid JSON only."

        if case_type == "battle":
            exclude_note = ""
            if exclude_cases:
                lines = "\n".join(f"- {c}" for c in exclude_cases[:30])
                exclude_note = (
                    f"\n\n⛔ НЕ ПОВТОРЯЙ эти позиции (они уже использовались):\n{lines}\n"
                    "Возьми другой угол зрения, аспект или противоречие на ту же тему."
                )

            user = f"""Создай дискуссию «Баттл» по теме "{topic}".
Нужно: 2 противоположные позиции с нюансами + итоговый синтез.

Материал:
{content[:3000]}{exclude_note}

Ответь ТОЛЬКО JSON:
```json
{{
  "cases": [
    {{
      "side": "A",
      "title": "Позиция А: ...",
      "description": "Развёрнутое описание позиции (2-3 предложения).",
      "key_arguments": ["Аргумент 1", "Аргумент 2", "Аргумент 3"],
      "nuance": "Слабое место или нюанс этой позиции (1 предложение)."
    }},
    {{
      "side": "B",
      "title": "Позиция Б: ...",
      "description": "Развёрнутое описание противоположной позиции (2-3 предложения).",
      "key_arguments": ["Аргумент 1", "Аргумент 2", "Аргумент 3"],
      "nuance": "Слабое место или нюанс этой позиции (1 предложение)."
    }}
  ],
  "synthesis": "Сбалансированный вывод, учитывающий обе позиции. Какова истина? (3-4 предложения)"
}}
```
Язык: {language}"""
            text = self._call(system, user, max_tokens=2000)
            data = self._parse_json(text)
            result = list(data["cases"])
            synthesis = data.get("synthesis", "")
            if synthesis:
                result.append({"side": "synthesis", "text": synthesis})
            if not exclude_cases:
                await set_cached("cases", result, topic=topic, content=content[:500], case_type=case_type, language=language)
            return result
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
            result = data["cases"]
            await set_cached("cases", result, topic=topic, content=content[:500], case_type=case_type, language=language)
            return result

    async def generate_flashcards(
        self, content, count=10, language="ru", exclude_terms=[]
    ) -> List[Dict[str, str]]:
        exclude_key = ",".join(sorted(exclude_terms)) if exclude_terms else ""
        cached = await get_cached("cards", content=content[:500], count=count, language=language, exclude=exclude_key)
        if cached:
            return cached

        exclude_note = ""
        if exclude_terms:
            exclude_note = f"\n\nНЕ включай эти термины (они уже были показаны): {', '.join(exclude_terms)}"

        system = "You are an educational content creator. Always respond with valid JSON only."
        user = f"""Извлеки {count} ключевых терминов и создай карточки из материала.{exclude_note}

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
        result = data["cards"]
        await set_cached("cards", result, content=content[:500], count=count, language=language, exclude=exclude_key)
        return result

    async def generate_reference_retelling(
        self, content, topic, language="ru"
    ) -> str:
        cached = await get_cached("retelling", content=content[:500], topic=topic, language=language)
        if cached:
            return cached

        system = "You are an expert educational assistant. Create structured, pedagogically sound summaries."
        user = f"""Создай подробный структурированный учебный отчёт по теме "{topic}".

Используй СТРОГО эту структуру (с заголовками ##):

## Краткое изложение
[3-5 предложений с главной идеей материала]

## Ключевые идеи
- [идея 1]
- [идея 2]
- [ещё идеи — минимум 4]

## Важные понятия
**[Термин 1]** — [краткое определение]
**[Термин 2]** — [краткое определение]

## Вывод
[1-2 предложения с главным выводом]

Материал:
{content[:4000]}

Язык: {language}"""

        result = self._call(system, user, max_tokens=1200)
        await set_cached("retelling", result, content=content[:500], topic=topic, language=language)
        return result

    async def chat_response(
        self, content, topic, history, message, language="ru"
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    f"Ты образовательный ИИ-помощник. Помогаешь разобрать тему «{topic}». "
                    f"Отвечай только по материалу ниже. Будь кратким и ясным. Язык ответа: {language}.\n\n"
                    f"Материал:\n{content[:3000]}"
                ),
            }
        ]
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=600,
        )
        return response.choices[0].message.content

    async def analyze_content(self, content, language="ru") -> Dict[str, Any]:
        cached = await get_cached("analyze", content=content[:500], language=language)
        if cached:
            return cached

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
        result = self._parse_json(text)
        await set_cached("analyze", result, content=content[:500], language=language)
        return result

    async def generate_extra_topics(
        self, content, main_topic, exclude_topics, count=5, language="ru"
    ) -> List[str]:
        system = "You are an educational content creator. Always respond with valid JSON only."
        exclude_str = "\n".join(f"- {t}" for t in exclude_topics)
        user = f"""Сгенерируй {count} новых подтем по теме "{main_topic}".

Материал:
{content[:2000]}

⛔ НЕ ПОВТОРЯЙ эти темы (они уже были использованы):
{exclude_str}

Придумай другие аспекты, углы зрения или подразделы той же темы.

Ответь ТОЛЬКО JSON:
```json
{{
  "topics": ["подтема 1", "подтема 2", ...]
}}
```
Язык: {language}"""

        text = self._call(system, user, max_tokens=400)
        data = self._parse_json(text)
        return data["topics"]

    async def health_check(self) -> bool:
        try:
            self._call("You are a helpful assistant.", "ping", max_tokens=5)
            return True
        except Exception:
            return False
