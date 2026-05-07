import json
import re
import httpx
from typing import List, Dict, Any
from app.config import settings
from .base import BaseAIProvider


class LocalProvider(BaseAIProvider):

    def __init__(self):
        self.base_url = settings.local_base_url
        self.model = settings.local_model_name
        self.timeout = settings.local_timeout

    def _parse_json(self, text: str) -> Any:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)

    async def _generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]

    async def generate_questions(
        self, topic, content, difficulty_levels, count=5, language="ru"
    ) -> List[Dict[str, Any]]:
        prompt = f"""Create {count} multiple choice questions about "{topic}" for levels: {", ".join(difficulty_levels)}.

Content: {content[:2000]}

Return ONLY JSON:
{{"questions": [{{"level": "easy|medium|hard", "question": "...", "answers": [{{"text": "...", "correct": true/false}}], "explanation": "..."}}]}}

Language: {language}"""
        text = await self._generate(prompt)
        data = self._parse_json(text)
        return data["questions"]

    async def generate_cases(
        self, topic, content, case_type, count=2, language="ru", exclude_cases=[]
    ) -> List[Dict[str, Any]]:
        prompt = f"""Create {count} cases for {case_type} about "{topic}".
Content: {content[:2000]}
Return ONLY JSON: {{"cases": [...]}}
Language: {language}"""
        text = await self._generate(prompt)
        data = self._parse_json(text)
        return data["cases"]

    async def generate_flashcards(
        self, content, count=10, language="ru", exclude_terms=[]
    ) -> List[Dict[str, str]]:
        exclude_note = f"\nDO NOT include these terms (already shown): {', '.join(exclude_terms)}" if exclude_terms else ""
        prompt = f"""Extract {count} key terms as flashcards.{exclude_note}
Content: {content[:2000]}
Return ONLY JSON: {{"cards": [{{"term": "...", "definition": "..."}}]}}
Language: {language}"""
        text = await self._generate(prompt)
        data = self._parse_json(text)
        return data["cards"]

    async def generate_reference_retelling(
        self, content, topic, language="ru"
    ) -> str:
        prompt = f"""Create a structured educational report about "{topic}" using these sections:
## Краткое изложение
## Ключевые идеи
## Важные понятия
## Вывод

Content: {content[:2000]}
Language: {language}"""
        return await self._generate(prompt)

    async def chat_response(
        self, content, topic, history, message, language="ru"
    ) -> str:
        context = "\n".join([f"{h['role'].capitalize()}: {h['content']}" for h in history[-5:]])
        prompt = f"""You are an AI tutor for topic "{topic}".
Material: {content[:1500]}
Previous conversation:
{context}
User: {message}
Answer briefly in {language}:"""
        return await self._generate(prompt)

    async def analyze_content(self, content, language="ru") -> Dict[str, Any]:
        prompt = f"""Analyze the educational content and return ONLY JSON:
{{"main_topic": "...", "subtopics": [], "key_concepts": [], "difficulty_estimate": "beginner|intermediate|advanced", "suggested_question_count": 10}}

Content: {content[:2000]}
Language: {language}"""
        text = await self._generate(prompt)
        return self._parse_json(text)

    async def generate_extra_topics(
        self, content, main_topic, exclude_topics, count=5, language="ru"
    ) -> List[str]:
        exclude_note = f"\nDO NOT repeat: {', '.join(exclude_topics)}" if exclude_topics else ""
        prompt = f"""Generate {count} new subtopics about "{main_topic}".{exclude_note}
Content: {content[:1500]}
Return ONLY JSON: {{"topics": ["topic 1", "topic 2", ...]}}
Language: {language}"""
        text = await self._generate(prompt)
        data = self._parse_json(text)
        return data["topics"]

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                return self.model in models
        except Exception:
            return False
