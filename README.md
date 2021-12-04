Welcome to guilded.py, a discord.py-esque asynchronous Python wrapper for the Guilded API. If you know discord.py, you know guilded.py.

## Documentation

In the works. Fortunately, if you've used discord.py before, you'll already have a head start.

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
        await message.channel.send('pong')

client.run('email', 'password')
```

For more examples, see the examples directory in this repository.

## Support

Enhanced-Guilded.py has a support channel under its dedicated group for any questions you may have.

Join the [Guilded.py](https://www.guilded.gg/i/kJObq4Op) server
