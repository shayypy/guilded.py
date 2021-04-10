from enum import Enum

class Presence(Enum):
    online = 1
    idle = 2
    dnd = 3
    do_not_disturb = dnd
    invisible = 4
    offline = invisible
    transparent = 5

    def __str__(self):
        return f'Presence.{self.name}'

    def __repr__(self):
        return f'<Presence value={self.value}>'

    def __int__(self):
        return self.value

    @classmethod
    def from_value(cls, value):
        return value_to_name.get(value, cls.transparent)

value_to_name = {
    1: Presence.online,
    2: Presence.idle,
    3: Presence.dnd,
    4: Presence.invisible,
    5: Presence.transparent
}
