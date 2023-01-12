import discord
import asyncio
import typing
import pathlib

import idlez.game
import idlez.store
from idlez import events


class IdleZBot(discord.Client):
    channel_name: str = "idlez"
    channel: dict[int, discord.TextChannel]
    store_path: pathlib.Path
    game: idlez.game.IdleZ

    def __init__(
        self,
        *,
        intents: discord.Intents,
        game: idlez.game.IdleZ,
        store_path: pathlib.Path,
        **kwargs,
    ):
        super().__init__(intents=intents, **kwargs)
        self.game = game
        self.store_path = store_path

        game.register_handler(self.on_game_event)

    async def setup_hook(self) -> None:
        # Invoke regular idlez ticks
        self.loop.create_task(self.idlez_game_task())
        self.loop.create_task(self.idlez_save_store())

    async def idlez_game_task(self):
        await self.wait_until_ready()
        last_tick = discord.utils.utcnow()
        while not self.is_closed():
            await asyncio.sleep(5)  # Sleep 5 seconds
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
        self.channel = dict()
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
        idlez_channel = self.channel.get(message.guild)
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
            f"{message.author.name}#{message.author.discriminator} has said something in {message.channel.name}: {message.content}"
        )

        try:
            self.game.make_noise(
                idlez.game.NoiseType.SPEAK, player_id=player_id, message=message.content
            )
        except idlez.game.PlayerNotFound:
            player = idlez.game.Player(
                id=player_id,
                name=message.author.nick,
                experience=0,
                level=0,
                guild_id=message.guild.id,
            )
            self.game.new_player(player)
            print(f"New player: {player}")

    async def send_to_player_group(self, player: idlez.store.Player, message: str):
        await self.channel[player.guild_id].send(message)

    async def on_game_event(self, evt: events.Event) -> None:
        if isinstance(evt, events.NewPlayerEvent):
            await self.send_to_player_group(
                evt.player,
                f"Your group hears a noise! After a closer look, {evt.player.name} peaks their head out. You fear the Z's might have heard them. Everyone loses {evt.exp_loss//10} experience.",
            )
        elif isinstance(evt, events.LevelUpEvent):
            await self.send_to_player_group(
                evt.player,
                f"The hiding from Z's paid off. Their experience took {evt.player.name} to level {evt.player.level}.",
            )
        elif isinstance(evt, events.BadPlayerEvent):
            if evt.event_type == events.EventType.LOUD_NOISE:
                await self.send_to_player_group(
                    evt.player,
                    f"{evt.player.name} trips on a bucket and falls into some metal junk. A terrible noise is heard and causes everyone to need to drop rations. Everyone loses {evt.exp_loss//10} experience.",
                )


def make_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


def run(
    token: str,
    intents: discord.Intents,
    game: idlez.game.IdleZ,
    store_path: pathlib.Path,
) -> None:
    client = IdleZBot(intents=intents, game=game, store_path=store_path)
    client.run(token)
