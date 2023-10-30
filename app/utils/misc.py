import os
import random

import whisper
import requests


async def wisper_detect(link: str):
    r = requests.get(link, allow_redirects=True)
    filename = f'{random.randint(10000000, 100000000)}.m4a'
    open(filename, 'wb').write(r.content)
    model = whisper.load_model("base")

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(filename)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    _, probs = model.detect_language(mel)
    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(model, mel, options)
    return result.text

