import discord
import asyncio
from typing import Any
import pathlib

import idlez.data
import idlez.game
import idlez.store
import idlez.events as events
import idlez.events.components as components
from idlez.store import GuildId


class IdleZBot(discord.Client):
    game: idlez.game.IdleZ
    store_path: pathlib.Path
    data: idlez.data.Data

    data_picker: idlez.data.DataPicker
    channel_name: str = "idlez"
    channel: dict[int, discord.TextChannel]

    def __init__(
        self,
        *,
        intents: discord.Intents,
        game: idlez.game.IdleZ,
        store_path: pathlib.Path,
        data: idlez.data.Data,
        **kwargs: Any,
    ):
        super().__init__(intents=intents, **kwargs)
        self.game = game
        self.store_path = store_path
        self.data = data
        self.channel: dict[GuildId, discord.TextChannel] = dict()
        self.data_picker = idlez.data.DataPicker(data)

        game.register_handler(self.on_game_event)
        game.player_idle_state_callback = self.get_player_idle_state

    def get_player_idle_state(
        self, player_id: int, guild_id: int
    ) -> idlez.game.IdleState:
        guild = self.get_guild(guild_id)
        if not guild:
            return idlez.game.IdleState.OFFLINE
        member = guild.get_member(player_id)
        if not member:
            return idlez.game.IdleState.OFFLINE
        if member.status == discord.Status.offline:
            return idlez.game.IdleState.OFFLINE
        elif member.status in [discord.Status.online, discord.Status.idle]:
            return idlez.game.IdleState.ONLINE
        return idlez.game.IdleState.AWAY

    async def setup_hook(self) -> None:
        # Invoke regular idlez ticks
        self.loop.create_task(self.idlez_game_task())
        self.loop.create_task(self.idlez_save_store())

    async def idlez_game_task(self):
        await self.wait_until_ready()
        last_tick = discord.utils.utcnow()
        while not self.is_closed():
            await asyncio.sleep(10)  # Sleep some seconds
            now = discord.utils.utcnow()
            diff, last_tick = now - last_tick, now
            await self.game.tick(diff.seconds)

    async def idlez_save_store(self):
        await self.wait_until_ready()
        while not self.is_closed():
            await asyncio.sleep(30)  # Sleep 30 seconds
            self.game.store.save(self.store_path)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        for guild in self.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                print(f"Found channel {channel.id} for guild {guild.id}")
                self.channel[guild.id] = channel

    async def on_message(self, message: discord.Message) -> None:
        if message.type != discord.MessageType.default:
            # Ignore non-default text messages
            return
        if message.author == self.user:
            # Ignore own messages
            return
        if message.author.bot or message.author.system:
            # Ignore bots and system users
            return
        if not message.guild:
            # Message has no guild, igoring
            return
        idlez_channel = self.channel.get(message.guild.id)
        if not idlez_channel:
            # Guild does not have an idlez channel set up.
            return
        if not (
            message.channel == idlez_channel
            or isinstance(message, discord.Thread)
            and message.parent == idlez_channel
        ):
            # Ignore messages / threads not in idlez channel
            return

        await self.on_idlez_message(message)

    async def on_idlez_message(self, message: discord.Message) -> None:
        player_id = message.author.id

        print(
            f"{message.author.name}#{message.author.discriminator} has said something: {message.content}"
        )

        try:
            self.game.make_noise(player_id=player_id)
        except idlez.game.PlayerNotFound:
            author = message.author
            nick = None
            if isinstance(author, discord.Member):
                nick = author.nick
            if not nick:
                nick = f"{author.name}#{author.discriminator}"

            if not message.guild:
                print(
                    "Cannot register user {nick} because message has no guild: {message}"
                )
                return

            player = idlez.game.Player(
                id=player_id,
                name=nick,
                experience=0,
                level=0,
                guild_id=message.guild.id,
            )
            self.game.new_player(player)
            print(f"New player: {player}")

    async def send_to_player_group(self, player: idlez.store.Player, message: str):
        await self.channel[player.guild_id].send(message)

    async def on_game_event(self, evt: events.Event) -> None:
        def exp_loss_str(exp_loss: components.ExpLossType) -> str:
            if isinstance(exp_loss, components.ExpLossFix):
                return str(exp_loss.loss_amount)
            elif isinstance(exp_loss, components.ExpLossProgress):
                percent = exp_loss.loss_percent
                if percent > 0.99:
                    return "all"
                elif percent > 0.8:
                    return "most"
                elif percent > 0.5:
                    return "a lot of"
                elif percent > 0.2:
                    return "some"
                else:
                    return "almost no"
            return "an unkown amount of"

        if isinstance(evt, events.LevelUpEvent):
            player = evt.component(components.Player).player
            total_secs_to_next_level = self.game.experience_for_level(player.level + 1)
            secs_to_next_level = total_secs_to_next_level - player.experience
            await self.send_to_player_group(
                player,
                self.data_picker.fill_event_message(
                    idlez.data.EventType.LEVEL_UP,
                    {
                        "player_name": player.name,
                        "new_level": player.level,
                        "ttl": human_secs(secs_to_next_level),
                    },
                ),
            )
        elif isinstance(evt, (events.NewPlayerEvent, events.PlayerNoiseEvent)):
            player = evt.component(components.Player).player
            exp_loss = evt.component(components.AllPlayerExpLoss).exp_loss

            if isinstance(evt, events.NewPlayerEvent):
                msg_type = idlez.data.EventType.NEW_PLAYER
            else:
                msg_type = idlez.data.EventType.LOUD_NOISE

            await self.send_to_player_group(
                player=player,
                message=self.data_picker.fill_event_message(
                    msg_type,
                    {
                        "player_name": player.name,
                        "exp_loss": exp_loss_str(exp_loss),
                    },
                ),
            )
        elif isinstance(evt, events.SinglePlayerEvent):
            player = evt.component(components.Player).player
            player_exp_diff_amount = evt.component(components.ExpEffect).exp_diffs.get(
                player.id, 0
            )
            message = evt.component(components.EventMessage).message
            await self.send_to_player_group(
                player,
                message.format_map(
                    {
                        "player_name": player.name,
                        "time_gain": human_secs(player_exp_diff_amount),
                    }
                ),
            )
        elif isinstance(evt, events.PlayerFightEvent):
            player = evt.component(components.Player).player
            other_player = evt.component(components.OtherPlayer).player
            player_wins = evt.component(components.FightResult).player_wins
            player_exp_diff_amount = evt.component(components.ExpEffect).exp_diffs.get(
                player.id, 0
            )
            await self.send_to_player_group(
                player=player,
                message=self.data_picker.fill_player_fight_message(
                    player_wins=player_wins,
                    params={
                        "player_name": player.name,
                        "other_player_name": other_player.name,
                        "time_diff": human_secs(abs(player_exp_diff_amount)),
                    },
                ),
            )


def human_secs(secs: int) -> str:
    MIN_SECS = 60
    HOUR_SECS = 60 * MIN_SECS
    DAY_SECS = 24 * HOUR_SECS

    days = secs // DAY_SECS
    secs -= days * DAY_SECS
    hours = secs // HOUR_SECS
    secs -= hours * HOUR_SECS
    mins = secs // MIN_SECS
    secs -= mins * MIN_SECS

    def pluralize(n: int, word: str) -> str:
        if n == 1:
            return f"1 {word}"
        return f"{n} {word}s"

    parts: list[str] = []
    if days > 0:
        parts.append(pluralize(days, "day"))
    if hours > 0:
        parts.append(pluralize(hours, "hour"))
    if mins > 0:
        parts.append(pluralize(mins, "minute"))
    if secs > 0:
        parts.append(pluralize(secs, "second"))

    return ", ".join(parts)


def make_intents() -> discord.Intents:
    intents = discord.Intents.all()
    return intents
