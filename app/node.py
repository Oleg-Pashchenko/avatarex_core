from app.sources.amocrm.execution import execute as amocrm_execute


def execute(params: dict, data: dict, source: str):
    if source == 'AmoCRM':
        amocrm_execute(params, data)

