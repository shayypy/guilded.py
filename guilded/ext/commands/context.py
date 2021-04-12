import guilded.abc


class Context(guilded.abc.Messageable):
    def __init__(self, **attrs):
        self.message = attrs.pop('message', None)
        self._state = attrs.pop('state', self.message._state)
        self.bot = attrs.pop('bot', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.prefix = attrs.pop('prefix')
        self.command = attrs.pop('command', None)
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_parents = attrs.pop('invoked_parents', [])
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)
        self.command_failed = attrs.pop('command_failed', False)

    @property
    def valid(self):
        return self.prefix is not None and self.command is not None

    @property
    def cog(self):
        if self.command is None:
            return None
        return self.command.cog

    @property
    def channel(self):
        return self.message.channel

    @property
    def _channel_id(self):
        return self.message.channel_id

    @property
    def team(self):
        return self.message.team

    @property
    def guild(self):
        return self.team

    @property
    def author(self):
        return self.message.author

    @property
    def me(self):
        return self.team.me if self.team else self.bot.user

    def reply(self, content, **kwargs):
        return self.message.reply(content, **kwargs)
