from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAIProvider(ABC):

    @abstractmethod
    async def generate_questions(
        self,
        topic: str,
        content: str,
        difficulty_levels: List[str],
        count: int = 5,
        language: str = "ru",
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
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def generate_flashcards(
        self,
        content: str,
        count: int = 10,
        language: str = "ru",
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
    async def health_check(self) -> bool:
        pass
