import guilded

# This is a guilded.py clone of the plain Node.js sample bot that Guilded
# provides, with a little extra spice.
# https://www.guilded.gg/docs/api/connecting

client = guilded.Client()

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

async def deal_with_message(message):
    if message.type is not guilded.MessageType.default or message.author.bot or not message.server:
        # Bots are allowed to say whatever they want, and we can't delete DM messages.
        return

    # This method assumes the bot has permission to do all of these things,
    # which it may not.
    if 'really bad word' in message.content:
        await message.author.ban(reason=f'Said a really bad word in #{message.channel.name}')
        await message.delete()

    elif 'bad word' in message.content:
        await message.reply('You can\'t say that!', private=True)
        await message.delete()

@client.event
async def on_message(message):
    await deal_with_message(message)

@client.event
async def on_message_update(before, after):
    await deal_with_message(after)

client.run('token')
