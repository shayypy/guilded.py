from .asset import Asset
from .file import File, MediaType
from .utils import ISO8601


class Group:
    def __init__(self, *, state, team, data):
        self._state = state
        self.team = team
        data = data.get('group', data)

        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.position = data.get('priority')

        self.game_id = data.get('gameId', 0)
        self.base = data.get('isBase')
        self.public = data.get('isPublic')
        
        self.created_by = self.team.get_member(data.get('createdBy')) or data.get('createdBy')
        self.updated_by = self.team.get_member(data.get('updatedBy')) or data.get('updatedBy')
        self.archived_by = self.team.get_member(data.get('archivedBy')) or data.get('archivedBy')

        self.created_at = ISO8601(data.get('createdAt'))
        self.updated_at = ISO8601(data.get('updatedAt'))
        self.deleted_at = ISO8601(data.get('deletedAt'))
        self.archived_at = ISO8601(data.get('archivedAt'))

        icon_url = data.get('avatar')
        if icon_url:
            self.icon_url = Asset('avatar', state=self._state, data=data)
        else:
            self.icon_url = None

        banner_url = data.get('banner')
        if banner_url:
            self.banner_url = Asset('banner', state=self._state, data=data)
        else:
            self.banner_url = None

    async def delete(self):
        return await self._state.delete_team_group(self.team.id, self.id)

    async def edit(self, **fields):
        if type(fields.get('icon')) == str:
            fields['icon_url'] = fields.get('icon')
        elif type(fields.get('icon')) == File:
            file = fields.get('icon')
            file.type = MediaType.group_icon
            fields['icon_url'] = await file._upload(self._state)
        elif type(fields.get('icon')) == type(None):
            fields['icon_url'] = None

        return await self._state.update_team_group(self.team.id, self.id, **fields)
