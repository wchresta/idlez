import os
import sys
import pathlib
import json
import importlib.resources
from typing import Optional
import argparse

import idlez


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="idleZ bot")
    parser.add_argument("--token-file", type=str)
    parser.add_argument("--data-dir", type=str, default="~/.local/share/idlez")
    parser.add_argument("--env-file", type=str, default=".env")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.env_file:
        load_dotenv(args.env_file)

    token = token_from_token_file(args.token_file)
    if not token:
        token = token_from_env(args.env_file)

    if not token:
        print("No token found, provide a token through IDLEZ_TOKEN", file=sys.stderr)
        sys.exit(1)

    store_path = pathlib.Path(args.data_dir).expanduser()
    store: idlez.game.Store
    try:
        store = idlez.game.Store.load(store_path)
    except FileNotFoundError:
        store_path.mkdir(parents=True, exist_ok=True)
        store = idlez.game.Store(players=dict())
        store.save(store_path)

    data = idlez.data.Data.from_lib_resources()
    game = idlez.game.IdleZ(store=store, data=data, event_handlers=[], event_queue=[])
    intents = idlez.bot.make_intents()
    bot = idlez.bot.IdleZBot(
        intents=intents, game=game, store_path=store_path, data=data
    )
    bot.run(token)
    store.save(store_path)


def token_from_token_file(token_file_path: str) -> Optional[str]:
    if not token_file_path:
        return None

    with open(token_file_path) as fh:
        return fh.readline().strip()


def token_from_env(env_file: str) -> Optional[str]:
    return os.getenv("IDLEZ_TOKEN")


def load_dotenv(env_file: str) -> None:
    if not os.path.exists(env_file):
        return

    with open(env_file) as fh:
        for line in fh:
            key, val = line.split("=")
            key = key.strip()
            val = val.strip()
            os.environ[key] = val
