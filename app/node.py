from app.sources.amocrm.execution import execute as amocrm_execute


async def execute(params: dict, data: dict, source: str):
    if source == 'AmoCRM':
        await amocrm_execute(params, data)

