import dataclasses
import json

import openai

from app.sources.amocrm.db import KnowledgeModeSettings, BoundedSituations
from app.utils import misc
from app.utils.db import MethodResponse, Message
import pandas as pd

descr = "Ищет соотвтествующий вопрос"


def perephrase(message, api_key,
               descr='Немного перфразируй сообщение. Оно должно быть презентабельным и полностью сохранять смысл. Ничего кроме того что есть в исходном сообщении быть не должно.'):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{"role": "system", "content": descr},
                      {'role': 'assistant', 'content': message}],
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
        properties = {}
        rq = []
        for r in first_row:
            if r in rq:
                continue
            rq.append(r)
            properties[r] = {'type': 'boolean', 'description': 'Вопрос соответствует заданному?'}

        return [{
            "name": "get_question_by_context",
            "description": descr,
            "parameters": {
                "type": "object",
                "properties": properties,
                'required': rq
            }
        }]

    @staticmethod
    def get_answer_by_question(questions, filename):
        answer = ''
        try:
            df = pd.read_excel(filename)
            list_of_arrays = list(df.iloc)
            for i in list_of_arrays:
                if i[0] == questions:
                    answer += i[1] + '\n'
                    break
        except:
            pass
        return answer

    @staticmethod
    def is_q_satisfy_q(q1, q2, openai_api_key):
        print('IS_Q_SATISFT')
        messages = [
            {'role': 'system', 'content': "Похож ли один вопрос на другой"},
            {"role": "user", "content": q1['args']},
            {"role": "user", "content": q2},
        ]
        func = [{
            "name": "is_questions_is_similar",
            "parameters": {
                "type": "object",
                "properties": {'is_similar': {'type': 'boolean', 'description': 'Являются ли 2 вопроса подобными'}},
                'required': ['is_similar']
            }
        }]
        openai.api_key = openai_api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=func,
            function_call={"name": "is_questions_is_similar"}
        )
        response_message = response["choices"][0]["message"]
        print("SATISFY", response_message)
        return response_message["function_call"]["arguments"]['is_similar']

    @staticmethod
    def get_keywords_values(message, func, openai_api_key):
        try:
            messages = [
                {'role': 'system', 'content': descr},
                {"role": "user",
                 "content": message}]
            openai.api_key = openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                functions=func,
                function_call={"name": "get_question_by_context"}
            )
            response_message = response["choices"][0]["message"]
        except Exception as e:
            print("ERROR", e)
            return {'is_ok': False, 'args': {}}
        if response_message.get("function_call"):
            function_args = json.loads(response_message["function_call"]["arguments"])
            print(function_args.keys())
            try:
                return {'is_ok': True, 'args': list(function_args.keys())[0]}
            except:
                return {'is_ok': False, 'args': []}
        else:
            return {'is_ok': False, 'args': []}

    @staticmethod
    def question_mode(user_message, filename, bounded_situations: BoundedSituations, openai_api_key):
        print('Получено сообщение:', user_message)
        func = KnowledgeMode.get_question_db_function(filename)
        response = KnowledgeMode.get_keywords_values(user_message, func, openai_api_key)
        print('RESPONSE', response)
        if not response['is_ok'] or not KnowledgeMode.is_q_satisfy_q(response, user_message, openai_api_key):
            return perephrase(bounded_situations.openai_error_message, openai_api_key)
        answer = KnowledgeMode.get_answer_by_question(response['args'], filename)

        if answer == '':
            return perephrase(bounded_situations.database_error_message, openai_api_key)

        return answer

    def execute(self, message, openai_api_key) -> MethodResponse:
        filename = misc.download_file(self.k_m_data.database_link)
        resp = KnowledgeMode.question_mode(message, filename, self.k_m_data.bounded_situations, openai_api_key)
        return MethodResponse(data=[Message(text=resp)], all_is_ok=True, errors=set())
