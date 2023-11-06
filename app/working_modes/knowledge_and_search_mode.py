import dataclasses

from app.utils.db import MethodResponse
from app.working_modes.common import Mode
from app.working_modes.knowledge_mode import KnowledgeMode
from app.working_modes.search_mode import SearchMode


@dataclasses.dataclass
class KnowledgeAndSearchMode:
    knowledge_mode: KnowledgeMode
    search_mode: SearchMode

    async def execute(self) -> MethodResponse:
        # Пытаемся найти информацию в базе данных
        response: MethodResponse = await self.search_mode.execute()

        if not response.all_is_ok:
            #  Если информацию в базе данных найти не удалось, пытаемся найти информацию в базе знаний
            response: MethodResponse = await self.knowledge_mode.execute()

        response.data = self.make_responses_unique(response.data)  # Удаляем повторые приветствия и другие повторения
        return response
