import datetime

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import dotenv
import psycopg2

dotenv.load_dotenv()

engine_core = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                       f'@{os.getenv("DB_HOST")}:5432/{os.getenv("DB_CORE_NAME")}')



Base = declarative_base()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database='avatarex_db',
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cur = conn.cursor()


class Leads(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer)
    status_id = Column(Integer)


class Messages(Base):
    id_id = Column(Integer, primary_key=True)
    __tablename__ = 'messages'
    id = Column(String(300))
    message = Column(String(10000))
    lead_id = Column(Integer, ForeignKey('leads.id'))
    is_bot = Column(Boolean)
    date = Column(DateTime)


class QualificationMode:
    id = ''
    q_rules = ''
    q_repeat_time = ''
    q_repeat_count = ''
    gpt_not_q_message_time = ''
    gpt_not_q_question_time = ''
    file_link = ''
    hi_message = ''
    openai_error_message = ''
    db_error_message = ''

    def __init__(self, pipeline_id):
        cur.execute("SELECT * FROM home_qualificationmode WHERE p_id=%s", (pipeline_id,))
        r = cur.fetchone()
        if len(r) == 0:
            return
        self.id, self.q_rules, self.q_repeat_time, self.q_repeat_count = r[1], r[2], r[3], r[4]
        self.gpt_not_q_message_time, self.gpt_not_q_question_time, self.file_link = r[5], r[6], r[7]
        self.hi_message, self.openai_error_message, self.db_error_message = r[8], r[9], r[10]


class RequestSettings:
    id = ''
    text = ''
    model = ''
    ft_model = ''
    tokens = ''
    temperature = ''
    voice = ''
    host = ''
    user = ''
    password = ''
    amo_key = ''
    openai_api_key = ''
    working_mode = ''
    view_rule = ''
    table_id = ''
    results_count = ''
    block_statuses = []
    qualification_mode = None

    def __init__(self, pipeline_id, user_id):
        self._get_data_from_amocrm_db_settings(user_id)
        self._get_data_from_amocrm_db_pipelines(pipeline_id)
        self._get_data_from_amocrm_db_statuses()
        self.qualification_mode = QualificationMode(pipeline_id)

    def _get_data_from_amocrm_db_statuses(self):
        cur.execute("SELECT * FROM home_statuses WHERE pipeline_id_id=%s", (self.table_id,))
        resp = cur.fetchall()
        statuses = []
        for r in resp:
            if r[4] is False:
                statuses.append(int(r[1]))
        self.block_statuses = statuses

    def _get_data_from_amocrm_db_pipelines(self, pipeline_id):
        cur.execute("SELECT * FROM home_pipelines WHERE p_id=%s", (pipeline_id,))
        resp = cur.fetchone()
        self.table_id = resp[1]
        self.working_mode = resp[0]
        self.id = resp[2]
        self.text = resp[3]
        self.model = resp[4]
        self.ft_model = resp[5]
        self.tokens = int(resp[6])
        self.temperature = float(resp[7])
        self.voice = bool(resp[8])
        self.filename = resp[11]
        self.work_rule = resp[12]
        self.file_link = resp[15]
        self.db_error_message = resp[16]
        self.hi_message = resp[17]
        self.openai_error_message = resp[18]
        self.success_message = resp[19]
        self.view_rule = resp[20]
        self.results_count = resp[21]

    def _get_data_from_amocrm_db_settings(self, user_id):
        cur.execute("SELECT * FROM home_amoconnect WHERE user_id=%s;", (user_id,))
        info = cur.fetchone()
        cur.execute('SELECT * FROM home_gptapikey WHERE user_id=%s;', (user_id,))
        info2 = cur.fetchone()
        self.openai_api_key = info2[1]
        self.user, self.password, self.host, self.amo_key = info[1], info[3], info[2], info[4]


# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine_core)
session = Session()


async def update_pipeline_information(r_d):
    try:
        if NEW_CLIENT_KEY in r_d.keys():
            lead_id, pipeline_id, status_id = r_d[UNSORTED_LEAD_ID_KEY], r_d[NEW_CLIENT_KEY], 0
        else:
            lead_id, pipeline_id, status_id = r_d[UPDATE_LEAD_ID_KEY], r_d[UPDATE_PIPELINE_KEY], \
                r_d[UPDATE_STATUS_ID_KEY]

        result = session.query(Leads).filter_by(id=lead_id).first()

        if result:
            result.pipeline_id, result.status_id = pipeline_id, status_id
        else:
            new_lead = Leads(id=lead_id, pipeline_id=pipeline_id, status_id=status_id)
            session.add(new_lead)
        session.commit()
    except:
        pass


async def get_messages(lead_id, request_settings: RequestSettings):
    message_objects = session.query(Messages).filter_by(lead_id=lead_id).all()[::-1]
    messages = []
    symbols = MODEL_16K_SIZE_VALUE if MODEL_16K_KEY in request_settings.model else MODEL_4K_SIZE_VALUE
    symbols = (symbols - request_settings.tokens) * 0.75 - len(request_settings.text)

    for message_obj in message_objects:
        if symbols - len(message_obj.message) <= 0:
            break
        if message_obj.is_bot:
            messages.append({'role': 'assistant', 'content': message_obj.message})
        else:
            messages.append({'role': 'user', 'content': message_obj.message})
        symbols = symbols - len(message_obj.message)
    messages = messages[::-1]
    messages.append({"role": "system", "content": request_settings.text})
    return messages


def get_bots_answers_count(lead_id) -> int:
    message_objects = session.query(Messages).filter_by(lead_id=lead_id).all()[::-1]
    count = 0
    for m in message_objects:
        if m.is_bot:
            count += 1

    return count


async def add_new_message(message_id, message, lead_id, is_bot):
    obj = Messages(id=message_id, message=message, lead_id=lead_id, is_bot=is_bot, date=datetime.datetime.now())
    session.add(obj)
    session.commit()


async def get_leads(lead_id):
    return session.query(Leads).filter_by(id=lead_id).first()


async def message_is_not_last(lead_id, message):
    return not session.query(Messages).filter_by(lead_id=lead_id, is_bot=False).all()[-1].message == message


async def clear_history(pipeline_id):
    result = session.query(Leads).filter_by(pipeline_id=pipeline_id).first()
    session.query(Messages).filter(Messages.lead_id == result.id).delete()
    session.commit()


async def message_already_exists(message_id):
    result = session.query(Messages).filter_by(id=message_id).first()
    return True if result else False


Base.metadata.create_all(engine_core)
