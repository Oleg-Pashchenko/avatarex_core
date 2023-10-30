import dataclasses

from app.working_modes.common import DatabaseModeData, Mode


@dataclasses.dataclass
class KnowledgeModeData:
    database_link: str
    d_m_data: DatabaseModeData



class KnowledgeMode(Mode):
    def __init__(self, data: KnowledgeAndSearchData, responses: list, errors: set):
        self.data: KnowledgeAndSearchData = data
        self.responses = responses
        self.errors = errors
        self.is_message_first = _is_message_first(self.data)

    async def execute(self) -> MethodResponse:
        qualification_mode = QualificationMode(data=self.data, responses=self.responses, errors=self.errors)

        if not qualification_mode.is_qualification_passed():
            #  Вызывается если есть неквалифицированные поля
            qualification_mode_result: MethodResponse = await qualification_mode.execute(
                is_message_first=self.is_message_first)