import asyncio
import guilded

# This is a showcase of the event style experiment.
# Read more here:
#   https://www.guilded.gg/guilded-api/blog/updates/Event-style-experiment
#   https://github.com/shayypy/guilded.py/issues/39

client = guilded.Client(experimental_event_style=True)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.event
async def on_message(event: guilded.MessageEvent):
    if event.message.content == 'ping':
        await event.message.channel.send('pong!')

    # This experiment also affects wait_for(), of course:
    elif event.message.content == '$wait':
        message = await event.message.channel.send("I'm waiting for a reaction to this message.")
        try:
            reaction_event = await client.wait_for(
                'message_reaction_add',
                check=lambda e: e.user_id == event.message.author_id and e.message_id == message.id,
                timeout=30
            )
        except asyncio.TimeoutError:
            pass
        else:
            await message.reply(f'You reacted with **{reaction_event.emote.name}**.')

@client.event
async def on_message_update(event: guilded.MessageUpdateEvent):
    if not event.before or event.before.content == event.after.content:
        # The content hasn't changed or we did not have it cached
        return

    # You should not actually do this
    diff = len(event.after.content) - len(event.before.content)
    await event.after.reply(f'You added {diff:,} characters to your message, nice job!')

@client.event
async def on_member_remove(event: guilded.MemberRemoveEvent):
    # In this example we pretend that every server wants member logs in their default channel

    if event.server.default_channel_id:
        channel = event.server.default_channel or await event.server.fetch_default_channel()
    else:
        return

    # Extra metadata
    if event.banned:
        cause = 'was banned from'
        colour = guilded.Colour.red()
    elif event.kicked:
        cause = 'was kicked from'
        colour = guilded.Colour.red()
    else:
        cause = 'has left'
        colour = guilded.Colour.gilded()

    embed = guilded.Embed(
        description=f'<@{event.user_id}> {cause} the server.',
        colour=colour,
    )
    await channel.send(embed=embed)

    # We also have `event.member` which will not be None if the member was cached prior to this event.
    # See also on_member_ban, which is a separate WebSocket event representing ban creation.

client.run('token')
