from app.sources.amocrm import db
from app.sources.amocrm.constants import *
import time
from app.sources.amocrm.methods import send_message


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

    # pipeline_settings = db.AvatarexSiteMethods.get_pipeline_settings()
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

    response_text = 'Это ответ'

    # if request_settings.working_mode == DEFAULT_WORKING_MODE:
    #    if await db.message_is_not_last(lead_id, message):
    #        return print('Сообщение не последнее! Обработка прервана!')

    send_message(user_id_hash, response_text, amocrm_settings)

    db.AvatarexDBMethods.add_message(message_id='', message=response_text, lead_id=lead_id, is_bot=True)

    return print('Сообщение отправлено!')
