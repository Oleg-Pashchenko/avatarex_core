from app.sources import amocrm


def execute(params: dict, data: dict, source: str):
    if source == 'AmoCRM':
        amocrm.methods.execute(params, data)

