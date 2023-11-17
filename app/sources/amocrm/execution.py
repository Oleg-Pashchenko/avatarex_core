from app.sources.amocrm import db
from app.sources.amocrm.constants import *
import time
from app.sources.amocrm.methods import send_message, fill_field
from app.sources.amocrm.new_amo import AmoConnect
from app.utils.db import Message, Command, MethodResponse
from app.working_modes.knowledge_and_search_mode import KnowledgeAndSearchMode
from app.working_modes.knowledge_mode import KnowledgeMode
from app.working_modes.prompt_mode import PromptMode
from app.working_modes.qualification_mode import QualificationMode
from app.working_modes.search_mode import SearchMode


def execute(params: dict, r_d: dict):
    owner_id = int(params['username'])

    if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
        db.AvatarexDBMethods.update_lead(r_d)
        return

    message_id = r_d[MESSAGE_ID_KEY]

    if int(r_d[MESSAGE_CREATION_KEY]) + 60 < int(time.time()):
        return print('Сообщение уже распознавалось!')

    print(f"Получено новое сообщение от user_id: {owner_id}")

    message, lead_id, user_id_hash = r_d[MESSAGE_KEY], r_d[LEAD_KEY], r_d[USER_ID_HASH_KEY]

    lead = db.AvatarexDBMethods.get_lead(lead_id)
    if lead is None:
        return print("Неккоректно установлен webhook!")

    amocrm_settings = db.AvatarexSiteMethods.get_amocrm_settings(owner_id=owner_id)
    pipeline_settings = db.AvatarexSiteMethods.get_pipeline_settings(pipeline_id=lead.pipeline_id)

    message_is_first: bool = False
    # request_settings = db.RequestSettings(lead.pipeline_id, username)

    if int(lead.status_id) not in pipeline_settings.work_statuses:
        return print("На данном статусе сделки бот не работает!")

    # if VOICE_MESSAGE_KEY in r_d.keys():
    #    if request_settings.voice:
    #        message = await misc.wisper_detect(r_d['message[add][0][attachment][link]'])
    #    else:
    #        return print('Отправлено голосовое, но распознование выключено!')

    if message == RESTART_KEY:
        db.AvatarexDBMethods.clear_messages_by_pipeline_id(lead.pipeline_id)
        return print('История успешно очищена!')

    qualification_mode = QualificationMode()
    qualification_mode_response, user_answer_is_correct, has_new = qualification_mode.execute_amocrm(pipeline_settings,
                                                                                                     amocrm_settings,
                                                                                                     lead_id,
                                                                                                     message,
                                                                                    db.AvatarexSiteMethods.get_gpt_key(
                                                                                                         owner_id)
                                                                                                     )
    print(amocrm_settings)
    amo_connection = AmoConnect(amocrm_settings.mail, amocrm_settings.password, host=amocrm_settings.host,
                                pipeline=pipeline_settings.pipeline_id, deal_id=lead_id)
    status = amo_connection.auth()
    print("Удалось ли установить соединение с амо:", status)
    if has_new is False and user_answer_is_correct is None:
        db.AvatarexDBMethods.add_message(message_id=message_id, message=message, lead_id=lead_id, is_bot=False)

        if pipeline_settings.chosen_work_mode == 'Ответ по контексту' or pipeline_settings.chosen_work_mode == 'Prompt mode':
            prompt_mode_data = db.AvatarexSiteMethods.get_prompt_method_data(pipeline_settings.p_mode_id)
            p_m = PromptMode(
                messages_history=db.AvatarexDBMethods.get_messages(lead_id, prompt_mode_data),
                tokens_limit=prompt_mode_data.max_tokens,
                temeperature=prompt_mode_data.temperature,
                model=prompt_mode_data.model,
                openai_api_key=db.AvatarexSiteMethods.get_gpt_key(owner_id)
            )
            response = p_m.execute()

        elif pipeline_settings.chosen_work_mode == 'Ответ из базы данных':
            print('я решил получить ответ из базы данных')
            s_m_data = db.AvatarexSiteMethods.get_search_method_data(pipeline_settings.s_mode_id)
            s_m = SearchMode(
                s_m_data=s_m_data
            )
            response = s_m.execute(message, db.AvatarexSiteMethods.get_gpt_key(owner_id))

        elif pipeline_settings.chosen_work_mode == 'Ответ из базы знаний':
            print('я решил получить ответ из базы знаний')
            k_m_data = db.AvatarexSiteMethods.get_knowledge_method_data(pipeline_settings.k_mode_id)
            k_m = KnowledgeMode(
                k_m_data=k_m_data
            )
            response = k_m.execute(message,
                                   db.AvatarexSiteMethods.get_gpt_key(owner_id))

        elif pipeline_settings.chosen_work_mode == 'Ответ из базы знаний и базы данных':
            response = MethodResponse(data=[Message(text="Метод не активен!")], all_is_ok=False, errors=set())

            print("я решил получить ответ из базы знаний и базы данных")
            k_s_m_data = db.AvatarexSiteMethods.get_knowledge_and_search_method_data(pipeline_settings.k_s_mode_id)
            k_s_m = KnowledgeAndSearchMode(
                knowledge_mode=k_s_m_data.knowledge_mode,
                search_mode=k_s_m_data.search_mode
            )
            response = k_s_m_data.execute(message,
                                          db.AvatarexSiteMethods.get_gpt_key(owner_id))

        else:
            response = MethodResponse(data=[Message(text="Ошибка выбора режима работы!")], all_is_ok=False,
                                      errors=set())

        # if request_settings.working_mode == DEFAULT_WORKING_MODE:
        #    if await db.message_is_not_last(lead_id, message):
        #        return print('Сообщение не последнее! Обработка прервана!')

        for entity in response.data:
            if isinstance(entity, Message):
                amo_connection.send_message(entity.text, user_id_hash)
                db.AvatarexDBMethods.add_message(message_id='', message=entity.text, lead_id=lead_id, is_bot=True)

    for entity in qualification_mode_response.data:
        if isinstance(entity, Message):
            amo_connection.send_message(entity.text, user_id_hash)
            # db.AvatarexDBMethods.add_message(message_id='', message=entity.text, lead_id=lead_id, is_bot=True)
        elif isinstance(entity, Command):
            if entity.command == 'fill':
                amo_connection.set_field_by_name(entity.data)

                # fill_field(entity.data['name'], entity.data['value'], amocrm_settings.host, amocrm_settings.mail,
                #           amocrm_settings.password, lead_id, pipeline_settings.pipeline_id)

    return print('Сообщение отправлено!')
