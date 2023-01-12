import dataclasses
import pathlib
import json


@dataclasses.dataclass(slots=True)
class Player:
    id: int
    name: str
    experience: int
    level: int
    guild_id: int


@dataclasses.dataclass
class Store:
    players: dict[int, Player]

    @staticmethod
    def player_file(store_path: pathlib.Path):
        return store_path.joinpath("players.jsonl")

    @classmethod
    def load(cls, path: pathlib.Path) -> "Store":
        players = dict()
        with open(cls.player_file(path), "r") as fh:
            for line in fh:
                player = Player(**json.loads(line))
                players[player.id] = player
        return cls(players=players)

    def save(self, path: pathlib.Path):
        with open(self.player_file(path), "w") as fh:
            for p in self.players.values():
                print(json.dumps(dataclasses.asdict(p)), file=fh)
