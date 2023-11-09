import dataclasses
import datetime
import random

import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
import os
import dotenv
from sqlalchemy.orm import sessionmaker

# from app.working_modes.common import DatabaseMode
# from app.working_modes.search_mode import SearchMode
# from app.working_modes.qualification_mode import QualificationModeData
# from app.working_modes.knowledge_mode import KnowledgeModeData
# from app.working_modes.prompt_mode import PromptMode
# from app.working_modes.knowledge_and_search_mode import KnowledgeAndSearchMode
from app.sources.amocrm.constants import *

dotenv.load_dotenv()

engine_core = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                            f'@{os.getenv("DB_HOST")}:5432/{os.getenv("AMO_BOT_DB_NAME")}')

conn = psycopg2.connect(
    dbname=os.getenv('SITE_DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST')
)
cur = conn.cursor()

Base = declarative_base()
Session = sessionmaker(bind=engine_core)
session = Session()


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


@dataclasses.dataclass
class AmocrmSettings:
    account_chat_id: str
    host: str
    mail: str
    password: str


@dataclasses.dataclass
class PipelineSettings:
    pipeline_id: int
    voice_message_detection: bool
    chosen_work_mode: str
    k_s_mode_id: int
    p_mode_id: int
    s_mode_id: int
    k_mode_id: int


@dataclasses.dataclass
class PromptModeSettings:
    context: str
    model: str
    max_tokens: int
    temperature: float
    qualification: dict
    qualification_finished: str


@dataclasses.dataclass
class BoundedSituations:
    hi_message: str
    openai_error_message: str
    database_error_message: str
    service_settings_error_message: str


@dataclasses.dataclass
class KnowledgeModeSettings:
    database_link: str
    bounded_situations: BoundedSituations
    qualification: dict
    qualification_finished: str


@dataclasses.dataclass
class SearchModeSettings:
    database_link: str
    search_rules: dict
    view_rule: str
    results_count: int
    bounded_situations: BoundedSituations
    qualification: dict
    qualification_finished: str


@dataclasses.dataclass
class KnowledgeAndSearchSettings:
    search_database_link: str
    knowledge_database_link: str
    search_rules: dict
    view_rule: str
    results_count: int
    bounded_situations: BoundedSituations
    qualification: dict
    qualification_finished: str


class AvatarexDBMethods:
    @staticmethod
    def update_lead(r_d):
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

    @staticmethod
    def get_lead(lead_id):
        return session.query(Leads).filter_by(id=lead_id).first()

    @staticmethod
    def get_messages(lead_id, prompt_mode_data):
        message_objects = session.query(Messages).filter_by(lead_id=lead_id).all()
        message_objects = sorted(message_objects, key=lambda x: x.date)

        messages = []
        # symbols = MODEL_16K_SIZE_VALUE if MODEL_16K_KEY in prompt_mode_data.model else MODEL_4K_SIZE_VALUE
        # symbols = (symbols - prompt_mode_data.max_tokens) * 0.75 - len(prompt_mode_data.context)

        for message_obj in message_objects:
            # if symbols - len(message_obj.message) <= 0:
            #    break
            if message_obj.is_bot:
                messages.append({'role': 'assistant', 'content': message_obj.message})
            else:
                messages.append({'role': 'user', 'content': message_obj.message})
            # symbols = symbols - len(message_obj.message)
        messages.insert(0, {"role": "system", "content": prompt_mode_data.context})

        return messages

    @staticmethod
    def add_message(message_id, message, lead_id, is_bot):
        if is_bot:
            message_id = f'assistant-{random.randint(1000000, 10000000)}'
        obj = Messages(id=message_id, message=message, lead_id=lead_id, is_bot=is_bot, date=datetime.datetime.now())
        session.add(obj)
        session.commit()

    @staticmethod
    def clear_messages_by_pipeline_id(pipeline_id):
        result = session.query(Leads).filter_by(pipeline_id=pipeline_id).first()
        session.query(Messages).filter(Messages.lead_id == result.id).delete()
        session.commit()


class AvatarexSiteMethods:
    @staticmethod
    def get_search_method_data(mode_id) -> SearchModeSettings:
        cur.execute(
            'SELECT database_link, search_rules, view_rule, results_count, mode_messages_id, qualification_id FROM home_searchmode WHERE id=%s;',
            (mode_id,))
        s_m_data = cur.fetchone()
        cur.execute(
            'SELECT hi_message, openai_error_message, database_error_message, service_settings_error_message FROM home_modemessages WHERE id=%s',
            (s_m_data[4],))
        b_s_data = cur.fetchone()
        q = AvatarexSiteMethods.get_qualification_data(s_m_data[5])
        return SearchModeSettings(
            database_link=s_m_data[0],
            search_rules=s_m_data[1],
            view_rule=s_m_data[2],
            results_count=s_m_data[3],
            bounded_situations=BoundedSituations(
                hi_message=b_s_data[0],
                openai_error_message=b_s_data[1],
                database_error_message=b_s_data[2],
                service_settings_error_message=b_s_data[3]
            ),
            qualification=q[0],
            qualification_finished=q[1]

        )  # Search method

    @staticmethod
    def get_knowledge_method_data(mode_id) -> KnowledgeModeSettings:
        cur.execute('SELECT database_link, mode_messages_id, qualification_id FROM home_knowledgemode WHERE id=%s;',
                    (mode_id,))
        k_m_data = cur.fetchone()
        cur.execute(
            'SELECT hi_message, openai_error_message, database_error_message, service_settings_error_message FROM home_modemessages WHERE id=%s',
            (k_m_data[1],))
        b_s_data = cur.fetchone()
        q = AvatarexSiteMethods.get_qualification_data(k_m_data[2])
        return KnowledgeModeSettings(
            database_link=k_m_data[0],
            bounded_situations=BoundedSituations(
                hi_message=b_s_data[0],
                openai_error_message=b_s_data[1],
                database_error_message=b_s_data[2],
                service_settings_error_message=b_s_data[3]
            ),
            qualification=q[0],
            qualification_finished=q[1]

        )  # Knowledge method

    @staticmethod
    def get_knowledge_and_search_method_data(k_s_search_mode_id):
        cur.execute("SELECT knowledge_mode_id, search_mode_id FROM home_searchandknowledgemode WHERE id=%s;",
                    (k_s_search_mode_id))
        k_s_m_data = cur.fetchone()
        search_mode_id, knowledge_mode_id = k_s_m_data[1], k_s_m_data[0]

        cur.execute('SELECT database_link FROM home_knowledgemode WHERE id=%s;',
                    (knowledge_mode_id,))
        k_m_data = cur.fetchone()
        cur.execute(
            'SELECT database_link, search_rules, view_rule, results_count, mode_messages_id, qualification_id FROM home_searchmode WHERE id=%s;',
            (search_mode_id,))
        s_m_data = cur.fetchone()
        cur.execute(
            'SELECT hi_message, openai_error_message, database_error_message, service_settings_error_message FROM home_modemessages WHERE id=%s',
            (s_m_data[4],))
        b_s_data = cur.fetchone()
        q = AvatarexSiteMethods.get_qualification_data(s_m_data[5])
        return KnowledgeAndSearchSettings(
            knowledge_database_link=k_m_data[0],
            search_database_link=s_m_data[0],
            search_rules=s_m_data[1],
            view_rule=s_m_data[2],
            results_count=s_m_data[3],
            bounded_situations=BoundedSituations(
                hi_message=b_s_data[0],
                openai_error_message=b_s_data[1],
                database_error_message=b_s_data[2],
                service_settings_error_message=b_s_data[3]
            ),
            qualification=q[0],
            qualification_finished=q[1]

        )  # Search method
        # Knowledge and search method

    @staticmethod
    def get_gpt_key(owner_id: int) -> str:
        cur.execute('SELECT key FROM home_gptapikey WHERE user_id=%s;', (owner_id,))
        return cur.fetchone()[0]

    @staticmethod
    def get_qualification_data(qualification_id) -> (dict, str):
        cur.execute("SELECT value, qualification_finished FROM home_modequalification WHERE id=%s",
                    (qualification_id,))  # Qualification data
        resp = cur.fetchone()
        qualification_value = resp[0]
        qualification_finished_value = resp[1]
        return qualification_value, qualification_finished_value

    @staticmethod
    def get_amocrm_settings(owner_id: int) -> AmocrmSettings:
        # Amocrm Settings
        cur.execute("SELECT account_chat_id, host, email, password FROM home_amoconnect WHERE user_id=%s;", (owner_id,))
        amocrm_connect_settings = cur.fetchone()
        return AmocrmSettings(
            account_chat_id=amocrm_connect_settings[0],
            host=amocrm_connect_settings[1],
            mail=amocrm_connect_settings[2],
            password=amocrm_connect_settings[3]
        )

    @staticmethod
    def get_pipeline_settings(pipeline_id: int) -> PipelineSettings:
        cur.execute('SELECT voice_message_detection, chosen_work_mode, knowledge_and_search_mode_id, '
                    'knowledge_mode_id, prompt_mode_id, search_mode_id FROM home_pipelines WHERE p_id=%s',
                    (pipeline_id,))
        pipeline_settings = cur.fetchone()
        return PipelineSettings(
            pipeline_id=pipeline_id,
            voice_message_detection=pipeline_settings[0],
            chosen_work_mode=pipeline_settings[1],
            k_s_mode_id=pipeline_settings[2],
            k_mode_id=pipeline_settings[3],
            p_mode_id=pipeline_settings[4],
            s_mode_id=pipeline_settings[5]
        )
        # Pipeline settings

    @staticmethod
    def get_prompt_method_data(mode_id: int):
        cur.execute('SELECT context, model, max_tokens, temperature, qualification_id FROM home_promptmode WHERE id=%s',
                    (mode_id,))
        prompt_mode_settings = cur.fetchone()  # Prompt method
        q = AvatarexSiteMethods.get_qualification_data(prompt_mode_settings[4])
        return PromptModeSettings(
            context=prompt_mode_settings[0],
            model=prompt_mode_settings[1],
            max_tokens=prompt_mode_settings[2],
            temperature=prompt_mode_settings[3],
            qualification=q[0],
            qualification_finished=q[1]
        )
