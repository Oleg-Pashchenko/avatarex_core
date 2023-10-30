import random

from app.sources.amocrm import db
from app.sources.amocrm.constants import *
from app.sources.amocrm.service import get_token
from app.utils import misc
import json
import time
import bs4
import requests



def send_notes(pipeline_id, text, host, mail, password):
    _, session, _ = get_token(host, mail, password)
    url = f'{host}private/notes/edit2.php?parent_element_id={pipeline_id}&parent_element_type=2'
    data = {
        'DATE_CREATE': int(time.time()),
        'ACTION': 'ADD_NOTE',
        'BODY': text,
        'ELEMENT_ID': pipeline_id,
        'ELEMENT_TYPE': '2'
    }
    resp = session.post(url, data=data)


def send_message(receiver_id: str, message: str, amocrm_settings: db.AmocrmSettings, token=''):
    while True:
        try:
            headers = {'X-Auth-Token': token}
            url = f'https://amojo.amocrm.ru/v1/chats/{amocrm_settings.account_chat_id}/' \
                  f'{receiver_id}/messages?with_video=true&stand=v15'
            response = requests.post(url, headers=headers, data=json.dumps({"text": message}))

            if response.status_code != 200:
                raise Exception("Токен не подошел!")
        except Exception:
            token, session, _ = get_token(amocrm_settings)
            continue
        break


def create_field(host: str, mail: str, password: str, name: str):
    token, session, headers = get_token(host, mail, password)

    url = f'{host}ajax/settings/custom_fields/'
    data = {
        'action': 'apply_changes',
        'cf[add][0][element_type]': 2,
        'cf[add][0][sortable]': True,
        'cf[add][0][groupable]': True,
        'cf[add][0][predefined]': False,
        'cf[add][0][type_id]': 1,
        'cf[add][0][name]': name,
        'cf[add][0][disabled]': '',
        'cf[add][0][settings][formula]': '',
        'cf[add][0][pipeline_id]': 0
    }
    session.post(url, headers=headers, data=data)


def get_field_by_name(name: str, host: str, mail: str, password: str, lead_id: int) -> (bool, int):
    url = f'{host}leads/detail/{lead_id}'
    token, session, headers = get_token(host, mail, password)
    response = session.get(url)
    if f'"NAME":"{name}"' not in response.text:
        return False, 0
    return True, int(response.text.split(f',"NAME":"{name}"')[0].split('"ID":')[-1])


def get_field_value_by_name(name: str, host: str, mail: str, password: str, lead_id: int) -> (bool, int):
    url = f'{host}leads/detail/{lead_id}'
    token, session, headers = get_token(host, mail, password)
    response = session.get(url)
    if f'"NAME":"{name}"' not in response.text:
        return False, 0

    param_id = int(response.text.split(f',"NAME":"{name}"')[0].split('"ID":')[-1])
    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    status = False
    try:
        value = soup.find('input', {'name': f'CFV[{param_id}]'})['value']

        if value == '':
            status = True
    except Exception as e:
        print(e)
    return status, 0


def set_field_by_name(param_id: int, host: str, mail: str, password: str, value: str, lead_id: int, pipeline_id: int):
    url = f'{host}ajax/leads/detail/'
    data = {
        f'CFV[{param_id}]': value,
        'lead[STATUS]': '',
        'lead[PIPELINE_ID]': pipeline_id,
        'ID': lead_id
    }
    token, session, headers = get_token(host, mail, password)
    response = session.post(url, headers=headers, data=data)
    print(response.text)


def fill_field(name, value, host, mail, password, lead_id, pipeline_id):
    exists, param_id = get_field_by_name(name, host, mail, password, lead_id)
    if not exists:
        create_field(host, mail, password, name)
        _, param_id = get_field_by_name(name, host, mail, password, lead_id)
    set_field_by_name(param_id, host, mail, password, value, lead_id, pipeline_id)


def get_field_info(q_m: db.QualificationMode, host, mail, password, lead_id):
    all_fields_qualified, first_uncompleted_field_description, second_uncompleted_field_description, first_field_name = True, '', '', ''
    for k in q_m.q_rules.keys():
        exists, field_id = get_field_value_by_name(k, host, mail, password, lead_id)
        if exists:
            all_fields_qualified = False
            if first_uncompleted_field_description == '':
                first_field_name = k
                first_uncompleted_field_description = q_m.q_rules[k]
            else:
                second_uncompleted_field_description = q_m.q_rules[k]
                break

    return all_fields_qualified, first_uncompleted_field_description, second_uncompleted_field_description, first_field_name


