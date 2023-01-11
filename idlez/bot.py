import discord
import typing

class IdleZBot(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')

def make_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    return intents

def run(token: str, intents: discord.Intents) -> typing.NoReturn:
    client = IdleZBot(intents=intents)
    client.run(token)

