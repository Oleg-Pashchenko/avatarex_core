from app.utils import err
from app.utils.db import MethodResponse, Message
from app.working_modes.common import DatabaseMode, Mode
from app.working_modes.qualification_mode import QualificationMode


class SearchMode(Mode):
    database_link: str
    search_rules: list[dict]
    view_rule: str
    results_count: int
    d_m: DatabaseMode
    q_m: QualificationMode

    def _is_file_format_qualify(self, file_path: str) -> bool:
        pass

    async def execute(self) -> MethodResponse:
        if self.is_message_first(self.d_m.messages_history):
            answer = await self.perephrase(self.d_m.hi_message, self.d_m.openai_api_key)
            self.method_response.data.append(Message(text=answer, is_hi_message=True))
            return self.method_response

        if not self.qualification_passed():
            # return self.q_m.
            return
        file_path, is_downloaded = await self.download_file(self.database_link)
        if not is_downloaded or not self._is_file_format_qualify(file_path):
            return self.method_response
