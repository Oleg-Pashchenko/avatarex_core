import json
import requests
import time
import bs4

from app.sources.amocrm.db import AmocrmSettings


def get_pipeline(image, s_name, text, time_string, host, mail, password):
    token, session, _ = get_token(host, mail, password)
    pipelines = json.load(open('config.json'))['pipelines']
    for pipeline in pipelines:
        pip1 = pipeline
        url = f'{host}leads/pipeline/{pipeline}/?skip_filter=Y'

        response = session.get(url, timeout=15)
        soup = bs4.BeautifulSoup(response.text, features='html.parser')
        for i in soup.find_all('div', {'class': 'pipeline-unsorted__item-data'}):
            img = i.find('div', {'class': 'pipeline-unsorted__item-avatar'}). \
                get('style').replace("background-image: url(", '').replace(')', '')
            message_time = i.find('div', {'class': 'pipeline-unsorted__item-date'}).text

            name = i.find('a', {'class': 'pipeline-unsorted__item-title'}).text
            message = i.find('div', {'class': 'pipeline_leads__linked-entities_last-message__text'}).text
            pipeline = i.find('a', {'class': 'pipeline-unsorted__item-title'}).get('href').split('/')[-1]
            if (img == image) or (message == text and s_name == name):
                return pipeline, pip1
    return None  # message[add][0][entity_id] || message[add][0][element_id]


def get_token(amocrm_settings: AmocrmSettings):
    host_2 = amocrm_settings.host.replace('https://', '').replace('/', '')
    try:
        session = requests.Session()
        response = session.get(amocrm_settings.host)
        session_id = response.cookies.get('session_id')
        csrf_token = response.cookies.get('csrf_token')
        headers = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': f'session_id={session_id}; '
                      f'csrf_token={csrf_token};'
                      f'last_login={amocrm_settings.mail}',
            'Host': amocrm_settings.host.replace('https://', '').replace('/', ''),
            'Origin': amocrm_settings.host,
            'Referer': amocrm_settings.host,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }
        payload = {
            'csrf_token': csrf_token,
            'password': amocrm_settings.password,
            'temporary_auth': "N",
            'username': amocrm_settings.mail}

        response = session.post(f'{amocrm_settings.host}oauth2/authorize', headers=headers, data=payload)
        access_token = response.cookies.get('access_token')
        refresh_token = response.cookies.get('refresh_token')
        headers['access_token'], headers['refresh_token'] = access_token, refresh_token
        payload = {'request[chats][session][action]': 'create'}
        headers['Host'] = host_2
        response = session.post(f'{amocrm_settings.host}ajax/v1/chats/session', headers=headers, data=payload)
        token = response.json()['response']['chats']['session']['access_token']
    except Exception as e:

        time.sleep(3)
        return get_token(amocrm_settings)

    return token, session, headers
