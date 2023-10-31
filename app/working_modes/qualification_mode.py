import dataclasses

from app.sources.amocrm import methods
from app.sources.amocrm.db import PipelineSettings, AvatarexSiteMethods, AmocrmSettings
from app.utils.db import MethodResponse, Command, Message


@dataclasses.dataclass
class QualificationMode:

    @staticmethod
    def _check_user_answer() -> (bool, Command | None):
        pass

    # 1) get first qualification field
    # 2) check qualification answer is correct or not
    # 3) is is correct form Command

    @staticmethod
    def _get_qualification_question(field_number) -> (str, bool):
        pass  # get

    @staticmethod
    def _is_qualification_passed(fields_to_fill: dict, source_fields: dict) -> bool:  # if > 0: get question
        for field_to_fill in fields_to_fill.keys():
            if field_to_fill not in source_fields.keys():  # Если поле не создано
                return True

            if source_fields[field_to_fill] is None:  # Если поле не заполнено
                return True
        return False

    def execute(self, fields_to_fill: dict, amocrm_settings: AmocrmSettings, lead_id: int) -> (
            MethodResponse, bool, bool):

        source_fields = methods.get_fields_info(amocrm_settings, lead_id, fields_to_fill)

        if len(fields_to_fill.keys()) == 0:  # если пользователь выставил что ничего заполнять не нужно
            return MethodResponse(data=[], all_is_ok=True, errors=set())

        if self._is_qualification_passed(fields_to_fill, source_fields):  # если квалификация уже пройдена
            return MethodResponse(data=[], all_is_ok=True, errors=set())

        # если все же мы остались здесь, значит нужно проверить ответ и задать квалифициирующий вопрос
        is_answer_correct, command = self._check_user_answer(user_answer, question)

        data = []
        if is_answer_correct:  # если ответ принят
            data.append(command)  # добавляем команду на заполнение поля
            message = self._get_qualification_question(2, source_fields)  # просим следующее сообщение
        else:
            message = self._get_qualification_question(1,source_fields, )  # повторяем текущий вопрос

        if message:  # если сообщение сформировалось
            data.append(message)

        return MethodResponse(all_is_ok=True, errors=set(), data=data), is_answer_correct, message is not None

    @staticmethod
    def execute_amocrm(pipeline_settings: PipelineSettings, amocrm_settings: AmocrmSettings,
                       lead_id: int) -> (MethodResponse, bool, bool):
        # временный костыль для AmoCRM
        if pipeline_settings.chosen_work_mode == 'Prompt mode':
            data = AvatarexSiteMethods.get_prompt_method_data(pipeline_settings.p_mode_id)
            return QualificationMode().execute(data.qualification, amocrm_settings, lead_id)


"""
@dataclasses.dataclass
class QualificationModeData:
    fields_to_fill: list[dict]
    d_m_data: DatabaseModeData


class QualificationMode:
    # Мод который вызывается в случае если is_qualification_passed - False

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
"""
