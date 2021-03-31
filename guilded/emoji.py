from .asset import Asset

class Emoji:
    def __init__(self, *, state, team, data):
        self._raw = data
        self._state = state
        self.team = team
        self.id = data.get('id')
        self.name = data.get('name')
        urls = {
            'customReaction': data.get('apng') or data.get('gif') or data.get('png') or data.get('webp'),
            # assume animated first, even though guilded seems to simply append ?ia=1 rather than using their apng field.
            'customReactionPNG': data.get('png'),
            'customReactionWEBP': data.get('webp'),
            'customReactionAPNG': data.get('apng'),
            'customReactionGIF': data.get('gif')
        }
        self.url = Asset('customReaction', state=self._state, data=urls)
        if getattr(self.url, 'apng') is not None or 'ia=1' in self.url:
            self.animated = True
        else:
            self.animated = False

    async def delete(self):
        return await self._state.delete_team_emoji(self.team.id, self.id)
