from app.sources.amocrm import db
from app.sources.amocrm.constants import *
import time
from app.sources.amocrm.methods import send_message
from app.utils.db import Message, Command
from app.working_modes.knowledge_mode import KnowledgeMode
from app.working_modes.prompt_mode import PromptMode
from app.working_modes.qualification_mode import QualificationMode


def execute(params: dict, r_d: dict):
    owner_id = int(params['username'])

    if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
        db.AvatarexDBMethods.update_lead(r_d)
        return print('Сделка успешно создана!')

    message_id = r_d[MESSAGE_ID_KEY]

    if int(r_d[MESSAGE_CREATION_KEY]) + 30 < int(time.time()):
        return print('Сообщение уже распознавалось!')

    message, lead_id, user_id_hash = r_d[MESSAGE_KEY], r_d[LEAD_KEY], r_d[USER_ID_HASH_KEY]
    print(lead_id, user_id_hash, message_id)
    lead = db.AvatarexDBMethods.get_lead(lead_id)
    amocrm_settings = db.AvatarexSiteMethods.get_amocrm_settings(owner_id=owner_id)
    pipeline_settings = db.AvatarexSiteMethods.get_pipeline_settings(pipeline_id=lead.pipeline_id)
    message_is_first: bool = False
    # request_settings = db.RequestSettings(lead.pipeline_id, username)

    # if int(lead.status_id) in request_settings.block_statuses:
    #    return print("На данном статусе сделки бот не работает!")

    # if VOICE_MESSAGE_KEY in r_d.keys():
    #    if request_settings.voice:
    #        message = await misc.wisper_detect(r_d['message[add][0][attachment][link]'])
    #    else:
    #        return print('Отправлено голосовое, но распознование выключено!')

    db.AvatarexDBMethods.add_message(message_id=message_id, message=message, lead_id=lead_id, is_bot=False)

    if message == RESTART_KEY:
        db.AvatarexDBMethods.clear_messages_by_pipeline_id(lead.pipeline_id)
        return print('История успешно очищена!')

    qualification_mode = QualificationMode()
    qualification_mode_response, user_answer_is_correct, has_new = qualification_mode.execute_amocrm(pipeline_settings,
                                                                                                     amocrm_settings,
                                                                                                     lead_id,
                                                                                                     message,
                                                                                                     db.AvatarexSiteMethods.get_gpt_key(
                                                                                                         owner_id))
    print(qualification_mode_response)

    # if not user_answer_is_correct or not has_new:
    if pipeline_settings.chosen_work_mode == 'Prompt mode':
        prompt_mode_data = db.AvatarexSiteMethods.get_prompt_method_data(pipeline_settings.p_mode_id)
        p_m = PromptMode(
            messages_history=db.AvatarexDBMethods.get_messages(lead_id, prompt_mode_data),
            tokens_limit=prompt_mode_data.max_tokens,
            temeperature=prompt_mode_data.temperature,
            model=prompt_mode_data.model,
            openai_api_key=db.AvatarexSiteMethods.get_gpt_key(owner_id)
        )
        response = p_m.execute()

    elif pipeline_settings.chosen_work_mode == 'Database mode':
        response = ""

    elif pipeline_settings.chosen_work_mode == 'Knowledge mode':
        k_m_data = db.AvatarexSiteMethods.get_knowledge_method_data(pipeline_settings.k_mode_id)
        k_m = KnowledgeMode(
            k_m_data=k_m_data
        )
        response = k_m.execute(message,
                               db.AvatarexSiteMethods.get_gpt_key(owner_id))

    else:
        response = 'Это ответ'

    # if request_settings.working_mode == DEFAULT_WORKING_MODE:
    #    if await db.message_is_not_last(lead_id, message):
    #        return print('Сообщение не последнее! Обработка прервана!')

    for entity in response.data:
        if isinstance(entity, Message):
            send_message(user_id_hash, entity.text, amocrm_settings)

    for entity in qualification_mode_response.data:
        if isinstance(entity, Message):
            send_message(user_id_hash, entity.text, amocrm_settings)

        elif isinstance(entity, Command):
            print('Command!')

    # db.AvatarexDBMethods.add_message(message_id='', message=response, lead_id=lead_id, is_bot=True)
    return print('Сообщение отправлено!')
