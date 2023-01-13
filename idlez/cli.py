import os
import sys
import pathlib
import json
import importlib.resources

import idlez


def main():
    load_dotenv()

    token = os.getenv("IDLEZ_TOKEN")
    if not token:
        print("No token found, provide a token through IDLEZ_TOKEN", file=sys.stderr)
        sys.exit(1)

    store_path = pathlib.Path("~/.local/share/idlez/").expanduser()
    store: idlez.game.Store
    try:
        store = idlez.game.Store.load(store_path)
    except FileNotFoundError:
        store_path.mkdir(parents=True, exist_ok=True)
        store = idlez.game.Store(players=dict())
        store.save(store_path)

    template = idlez.bot.Template(
        templates=json.loads(
            importlib.resources.read_text("idlez.data", "messages.json")
        )
    )
    game = idlez.game.IdleZ(store=store, event_handlers=[], event_queue=[])
    intents = idlez.bot.make_intents()
    idlez.bot.run(
        token=token,
        intents=intents,
        game=game,
        store_path=store_path,
        template=template,
    )
    store.save(store_path)


def load_dotenv():
    if not os.path.exists(".env"):
        return

    with open(".env") as fh:
        for line in fh:
            key, val = line.split("=")
            key = key.strip()
            val = val.strip()
            os.environ[key] = val
