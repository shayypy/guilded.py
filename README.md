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

Guilded.py has a support channel under its dedicated group for any questions you may have.

1. Join the [Guilded-API](https://community.guildedapi.com) server
2. Navigate to #library-list
3. Click on the guilded.py role and click "Add me to role"
4. You should see a new group pop up in your sidebar - you are now in the Guilded.py group
