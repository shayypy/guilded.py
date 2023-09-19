import re
import guilded
from guilded.ext import commands

# Generic database-less ticket bot that makes use of role & user permission overrides.
# In a real bot, you would usually want to store ticket information locally as well as
# restrict ticket creation. This example also only works in one server as the category
# and moderator role IDs are hardcoded.

TICKET_CATEGORY_ID = 0
MOD_ROLE_ID = 0
TICKET_REGEX = r"^((?:✅|❌) )?\[\w{8,}\] .+$"

bot = commands.Bot(
    command_prefix="t/",
    help_command=commands.MinimalHelpCommand(),
)


@bot.event
async def on_ready():
    print(f"{bot.user} ready ({bot.user_id})")


@bot.command()
@commands.server_only()
async def ticket(ctx: commands.Context, *, message: str = None):
    channel = await ctx.server.create_chat_channel(
        f"[{ctx.author.id}] {ctx.author.name}"[:100],
        topic=message[:512] if message else None,
        category=guilded.Object(TICKET_CATEGORY_ID),
    )
    if not ctx.server.base_role:
        await ctx.server.fill_roles()

    # Your particular implementation might prefer to set these first two
    # overrides on the category level instead, which would be faster.
    await channel.create_role_override(
        ctx.server.base_role,
        guilded.PermissionOverride(
            read_messages=False,
            send_messages=False,
        ),
    )
    # We assume the bot also has this role or isn't otherwise going to be
    # forbidden from modifying the channel after the first override.
    await channel.create_role_override(
        guilded.Object(MOD_ROLE_ID),
        guilded.PermissionOverride(
            read_messages=True,
            send_messages=True,
        ),
    )

    await channel.send(
        embed=guilded.Embed(
            title=f"Ticket for {ctx.author.mention}",
            description=f"Message: {message}"[:2048]
            if message
            else "No message given - please follow up with details.",
        )
        .set_thumbnail(url=ctx.author.display_avatar)
        .add_field(
            name="For moderators",
            value=(
                f"- `{ctx.prefix}resolve` to mark the ticket as resolved.\n"
                f"- `{ctx.prefix}close [reason]` to just close the ticket."
            ),
            inline=False,
        )
    )

    await channel.create_user_override(
        ctx.author,
        guilded.PermissionOverride(
            read_messages=True,
            send_messages=True,
        ),
    )

    await ctx.reply(
        f"Ticket created in [#{channel.name}]({channel.jump_url}).",
        private=True,
    )


@bot.command()
@commands.has_role(MOD_ROLE_ID)
async def resolve(ctx: commands.Context):
    # Guilded does not allow you to fetch all channels in a server,
    # so we can't do something like passing the user to close their
    # ticket(s). If you stored your tickets in a database this would
    # be more straightforward.

    match = re.match(TICKET_REGEX, ctx.channel.name)
    if not match or ctx.channel.category_id != TICKET_CATEGORY_ID:
        await ctx.reply("This is not a ticket channel.", private=True)
        return

    emoji = match[1]
    if emoji:
        name = ctx.channel.name.replace(emoji, "")
    else:
        name = ctx.channel.name

    await ctx.channel.edit(name=f"✅ {name}")

    # ... Do more stuff


@bot.command()
@commands.has_role(MOD_ROLE_ID)
async def close(ctx: commands.Context):
    # See `resolve` comment

    match = re.match(TICKET_REGEX, ctx.channel.name)
    if not match or ctx.channel.category_id != TICKET_CATEGORY_ID:
        await ctx.reply("This is not a ticket channel.", private=True)
        return

    emoji = match[1]
    if emoji:
        name = ctx.channel.name.replace(emoji, "")
    else:
        name = ctx.channel.name

    await ctx.channel.edit(name=f"❌ {name}")

    # ... Do more stuff


bot.run("token")
