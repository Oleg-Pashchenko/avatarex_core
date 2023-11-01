import dataclasses
import json

import openai

from app.sources.amocrm.db import KnowledgeModeSettings, BoundedSituations
from app.utils import misc
from app.utils.db import MethodResponse, Message
import pandas as pd


def perephrase(message, api_key):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{"role": "system", "content": 'Перефразируй'},
                      {'role': 'user', 'content': message}],
            max_tokens=4000,
            temperature=1
        )
        return response['choices'][0]['message']['content']
    except:
        return message


@dataclasses.dataclass
class KnowledgeMode:
    k_m_data: KnowledgeModeSettings

    @staticmethod
    def get_question_db_function(filename):
        df = pd.read_excel(filename)
        first_row = list(df.iloc[:, 0])
        return [{
            "name": "Function",
            "description": "Get flat request",
            "parameters": {
                "type": "object",
                "properties": {'Question': {'type': 'string', 'enum': first_row}},
                'required': ['Question']
            }
        }]

    @staticmethod
    def get_answer_by_question(question, filename):
        answer = None
        try:
            df = pd.read_excel(filename)
            list_of_arrays = list(df.iloc)
            for i in list_of_arrays:
                if i[0] == question:
                    answer = i[1]
                    break
        except:
            pass
        return answer

    @staticmethod
    def get_keywords_values(message, func, openai_api_key):
        try:
            messages = [
                {'role': 'system', 'content': 'Give answer:'},
                {"role": "user",
                 "content": message}]
            openai.api_key = openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
                functions=func,
                function_call="auto"
            )
            response_message = response["choices"][0]["message"]
        except:
            return {'is_ok': False, 'args': {}}
        if response_message.get("function_call"):
            function_args = json.loads(response_message["function_call"]["arguments"])
            return {'is_ok': True, 'args': function_args}
        else:
            return {'is_ok': False, 'args': {}}

    @staticmethod
    def question_mode(user_message, filename, bounded_situations: BoundedSituations, openai_api_key):
        print('Получено сообщение:', user_message)
        func = KnowledgeMode.get_question_db_function(filename)
        response = KnowledgeMode.get_keywords_values(user_message, func, openai_api_key)

        if not response['is_ok']:
            return perephrase(bounded_situations.openai_error_message, openai_api_key)
        answer = KnowledgeMode.get_answer_by_question(response['args']['Question'], filename)
        if answer is None:
            return perephrase(bounded_situations.database_error_message, openai_api_key)
        print("Квалифицирован вопрос:", response['args']['Question'])
        print('Получен ответ из базы данных:', answer)
        response = perephrase(answer, openai_api_key)
        print('Перефразирован ответ:', response)
        return response

    def execute(self, message, openai_api_key) -> MethodResponse:
        filename = misc.download_file(self.k_m_data.database_link)
        resp = KnowledgeMode.question_mode(message, filename, self.k_m_data.bounded_situations, openai_api_key)
        return MethodResponse(data=[Message(text=resp)], all_is_ok=True, errors=set())
