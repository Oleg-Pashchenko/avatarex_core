import dataclasses

from app.working_modes.common import DatabaseModeData


@dataclasses.dataclass
class QualificationModeData:
    fields_to_fill: list[dict]
    d_m_data: DatabaseModeData


class QualificationMode:
    """Мод который вызывается в случае если is_qualification_passed - False"""

    def __init__(self, data: KnowledgeAndSearchData, responses: list, errors: set):
        self.data: KnowledgeAndSearchData = data
        self.responses: list[Message | Command] = responses
        self.errors = errors

    async def is_qualification_passed(self) -> bool:  # if > 0: get question
        fields_to_fill = self.data.fields_to_fill
        for field in fields_to_fill:
            if not field['exists']:
                return False
        return True

    async def _is_qualification_question_answer_satisfy(self) -> bool:
        pass

    async def _get_unfiled_field(self, position_index: int) -> (dict, None):
        pass

    async def _create_question(self, unfiled_field: dict) -> bool:
        answer, status = _perephrase(message=unfiled_field['question'], data=self.data)

        if status:
            self.responses.append(Message(text=answer, set_last_order=True))
        else:
            self.responses.append(Message(text=unfiled_field['question'], set_last_order=True))
            self.errors.add(err.OPENAI_REQUEST_ERROR)
        return status

    async def execute(self):
        unfiled_field = await self._get_unfiled_field(1)  # получаем первое незаполненное поле
        if unfiled_field is None:  # если все поля заполнены
            return SearchMode(data=self.data, responses=self.responses, errors=self.errors).execute()

        if self.is_message_first:  # если это первое сообщение от клиента
            status = await self._create_question(unfiled_field=unfiled_field)
            return MethodResponse(data=self.responses, all_is_ok=status, errors=self.errors)

        unfiled_field = await self._get_unfiled_field(2)  # получаем второе незаполненное поле
        if unfiled_field is None:  # если все поля заполнены
            return SearchMode(data=self.data, responses=self.responses, errors=self.errors,
                              ).execute()

        else:
            if not await self._is_qualification_question_answer_satisfy():
                # если мы посчитали что ответ на вопрос не был дан или был дан некорректно
                return SearchMode(data=self.data, responses=self.responses, errors=self.errors,
                                  ).execute()
            else:
                # если ответ нас устроил
                self.responses.append(Command(command='fill', data=unfiled_field))
                status = await self._create_question(unfiled_field=unfiled_field)  # Создаем новый вопрос
                return MethodResponse(data=self.responses, all_is_ok=status, errors=self.errors)
