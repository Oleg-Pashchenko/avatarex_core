import dataclasses
import openai

from app.utils import err
from app.utils.db import MethodResponse, Message
from app.working_modes.common import Mode


@dataclasses.dataclass
class PromptMode:
    messages_history: list
    tokens_limit: int
    temeperature: float
    model: str
    openai_api_key: str

    def execute(self) -> MethodResponse:
        try:
            openai.api_key = self.openai_api_key
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages_history,
                max_tokens=self.tokens_limit,
                temperature=self.temeperature
            )
            result = MethodResponse(all_is_ok=True,
                                    data=[Message(text=response['choices'][0]['message']['content'])], errors=set())
        except Exception as e:
            print('Prompt mode exception:', e)
            result = MethodResponse(all_is_ok=False, data=[], errors=set(err.OPENAI_REQUEST_ERROR))
        return result
