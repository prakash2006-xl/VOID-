import re
import asyncio
from dodaios.plugins.tts.piper_local import PiperLocalTTS

def clean_text_for_speech(text: str) -> str:
    if not text:
        return ""
    s = text
    s = re.sub(r"<tool_call>.*?</tool_call>", "", s, flags=re.DOTALL)
    s = re.sub(r"<function=[^>]+>", "", s)
    s = re.sub(r"<parameter=[^>]+>", "", s)
    s = re.sub(r"</?[a-zA-Z0-9_-]+>", "", s)
    s = re.sub(r"\b([a-z]+)_([a-z]+)\b", r"\1 \2", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"https?://\S+", "the link", s)
    s = re.sub(r"/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)+", "the file", s)
    s = re.sub(r"[\U00010000-\U0010ffff]", "", s)
    s = re.sub(r"[⏱️🎧💭💬💙🎉💫☀️🌙🌤️]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

test_text = "Who would you like to send the email to? Please type the recipient's email address below, or speak it. 💫"
cleaned = clean_text_for_speech(test_text)
print("Cleaned text:", repr(cleaned))

async def test():
    tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=1.0)
    total = 0
    async for chunk in tts.synthesize(cleaned):
        total += len(chunk.pcm)
    dur = (total // 2) / 22050
    wpm = (len(cleaned.split()) / dur) * 60
    print(f"Duration: {dur:.2f}s, WPM: {wpm:.1f}")

asyncio.run(test())
