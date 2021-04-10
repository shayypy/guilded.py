import logging

log = logging.getLogger(__name__)

class TransientStatus:
    def __init__(self, *, state, data, **extra):
        self.id = data.get('id')
        self.game_id = data.get('id')

class Game:
    MAPPING = {}
    def __init__(self, id: int):
        if not self.MAPPING:
            log.warning('The internal game cache is empty. Call coroutine client.fill_game_list to fill it automatically.')

        self.id = id
        self.name = self.MAPPING.get(str(id))

    def __str__(self):
        return self.name
