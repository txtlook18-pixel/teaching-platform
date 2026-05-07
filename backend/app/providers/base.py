from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseAIProvider(ABC):

    @abstractmethod
    async def generate_questions(
        self,
        topic: str,
        content: str,
        difficulty_levels: List[str],
        count: int = 5,
        language: str = "ru",
        exclude_questions: List[str] = [],
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def generate_cases(
        self,
        topic: str,
        content: str,
        case_type: str,
        count: int = 2,
        language: str = "ru",
        exclude_cases: List[str] = [],
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def generate_flashcards(
        self,
        content: str,
        count: int = 10,
        language: str = "ru",
        exclude_terms: List[str] = [],
    ) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def generate_reference_retelling(
        self,
        content: str,
        topic: str,
        language: str = "ru",
    ) -> str:
        pass

    @abstractmethod
    async def analyze_content(
        self,
        content: str,
        language: str = "ru",
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def chat_response(
        self,
        content: str,
        topic: str,
        history: List[Dict[str, str]],
        message: str,
        language: str = "ru",
    ) -> str:
        pass

    @abstractmethod
    async def generate_extra_topics(
        self,
        content: str,
        main_topic: str,
        exclude_topics: List[str],
        count: int = 5,
        language: str = "ru",
    ) -> List[str]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
