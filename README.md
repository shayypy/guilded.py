Welcome to guilded.py, a discord.py-esque asynchronous Python wrapper for Guilded's bot API. If you know discord.py, you know guilded.py.

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

Join the guilded.py server for help & discussion. Use the #library-help channel.

[![shield](https://shields.yoki-labs.xyz/shields/vanity/gpy)](https://guilded.gg/gpy)
