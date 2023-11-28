import dataclasses
import os

import openai

from app.utils import err
from app.utils.db import MethodResponse, Message
from openai import AsyncOpenAI


@dataclasses.dataclass
class PromptMode:
    messages_history: list
    tokens_limit: int
    temeperature: float
    model: str
    openai_api_key: str

    async def execute(self) -> MethodResponse:
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        client = AsyncOpenAI()
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=self.messages_history,
                timeout=20
                # max_tokens=self.tokens_limit,
                # temperature=self.temeperature
            )
            result = MethodResponse(all_is_ok=True,
                                    data=[Message(text=response.choices[0].message.content)], errors=set())
        except Exception as e:
            print(e)
            result = MethodResponse(all_is_ok=False, data=[], errors=err.OPENAI_REQUEST_ERROR)
        print("Результат получен", result)
        return result
