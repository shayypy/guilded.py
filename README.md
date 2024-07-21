Welcome to guilded.py, a discord.py-esque asynchronous Python wrapper for Guilded's bot API. If you know discord.py, you know guilded.py.

## Warning

Due to the fallout of [Guilded's login change](https://www.guilded.gg/blog/update-to-guilded-login-requirements), this project will not be seeing much maintenance. This is in conjunction with the API itself getting little attention lately. As such, you may want to coordinate with me [on Discord](#support) to update the library.

## Documentation

Documentation is available on [Read the Docs](https://guildedpy.readthedocs.io).

## Basic Example

```py
import guilded

client = guilded.Client()

@client.event
async def on_ready():
    print('Ready')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == 'ping':
        await message.channel.send('pong!')

client.run('token')
```

### Bot example

```py
import guilded
from guilded.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

bot.run('token')
```

For more examples, see the examples directory in this repository.

## Support

I am reachable on [Discord](https://discord.com/invite/m4BqzUx72w).
