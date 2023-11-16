from quart import Quart, request
import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from app import node


application = Quart(__name__)


@application.route('/api/v1/amocrm/<username>', methods=['POST'])
async def amo_request_handler(username):
    data = dict(await request.values)
    node.execute(params={'username': username}, data=data, source='AmoCRM')
    return 'ok'


@application.route('/', methods=['GET'])
async def hi_handler():
    return 'All is fine!'


@application.route('/api/v1/tests', methods=['POST'])
async def tests_request_handler():
    data = dict(await request.values)
    node.execute(params={}, data=data, source='tests')
    return 'ok'


if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:8081"]
    asyncio.run(serve(application, config))
