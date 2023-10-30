import dataclasses


class Message:
    text: str = ''
    is_hi_message: bool = False

    def __init__(self, text: str):
        self.text = text

    def __init__(self, text: str, is_hi_message: bool):
        self.text = text
        self.is_hi_message = is_hi_message


@dataclasses.dataclass
class Command:
    command: str
    data: dict


@dataclasses.dataclass
class MethodResponse:
    data: list[Message | Command]
    all_is_ok: bool
    errors: set
