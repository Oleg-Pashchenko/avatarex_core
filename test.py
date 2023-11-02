import openai
import pandas as pd
import openpyxl


openai.api_key = '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'


def get_func(filename):
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


func = get_func('test.xlsx')
message = 'Какая программа обучения предлагается в вашей онлайн-школе?'
messages = [
    {'role': 'system', 'content': 'У тебя есть функция. Выполни ее'},
    {"role": "user",
     "content": message}]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-0613",
    messages=messages,
    functions=func,
    function_call="auto"
)
print(response)
