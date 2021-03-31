class Activity:
    '''Represents a user or member's activity in Guilded. Referred to as "Status" in the user popout.'''
    def __init__(self, *, details: str):
        self.details = details

    @classmethod
    def build(cls, data):
        pl = data
        return cls(details=pl.get('content'))
