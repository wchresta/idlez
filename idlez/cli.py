import os
import sys
from idlez import bot

def main():
    load_dotenv()

    token = os.getenv("IDLEZ_TOKEN")
    if not token:
        print("No token found, provide a token through IDLEZ_TOKEN", file=sys.stderr)

    intents = bot.make_intents()
    bot.run(token, intents)

def load_dotenv():
    if not os.path.exists(".env"):
        return

    with open(".env") as fh:
        for line in fh:
            key, val = line.split("=")
            key = key.strip()
            val = val.strip()
            os.environ[key] = val

