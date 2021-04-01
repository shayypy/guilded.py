# This is a development branch

This is not the main branch of guilded.py. Breaking changes ensue. This branch is not on PyPI. Please [join the Guilded API server](https://community.guildedapi.com) to give feedback (#library-list, guilded.py role).

### Basic Example

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
        await message.channel.send('pong')  # per #updates, message.channel will sometimes be None due to caching issues

client.run('email@example.com', 'password123')
```