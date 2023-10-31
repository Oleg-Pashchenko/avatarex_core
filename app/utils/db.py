import dataclasses


class Message:
    text: str = ''
    is_hi_message: bool = False

    def __init__(self, text: str):
        self.text = text


@dataclasses.dataclass
class Command:
    command: str
    data: dict


@dataclasses.dataclass
class MethodResponse:
    data: list[Message | Command]
    all_is_ok: bool
    errors: set
