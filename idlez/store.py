import dataclasses
import pathlib
import json

PlayerId = int
Experience = int
Level = int
GuildId = int


@dataclasses.dataclass(slots=True)
class Player:
    id: PlayerId
    name: str
    experience: Experience
    level: Level
    guild_id: GuildId


@dataclasses.dataclass
class Store:
    players: dict[PlayerId, Player]

    @staticmethod
    def player_file(store_path: pathlib.Path):
        return store_path.joinpath("players.jsonl")

    @classmethod
    def load(cls, path: pathlib.Path) -> "Store":
        players: dict[PlayerId, Player] = dict()
        with open(cls.player_file(path), "r") as fh:
            for line in fh:
                player = Player(**json.loads(line))
                players[player.id] = player
        return cls(players=players)

    def save(self, path: pathlib.Path):
        with open(self.player_file(path), "w") as fh:
            for p in self.players.values():
                print(json.dumps(dataclasses.asdict(p)), file=fh)
