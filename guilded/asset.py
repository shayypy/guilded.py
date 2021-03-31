class Asset:
    FRIENDLY = {
        'sm': 'small',
        'md': 'medium',
        'lg': 'large'
    }
    def __init__(self, type, *, state, data):
        self._state = state
        self.type = type

        self.url = data.get(self.type)
        for key, value in data.items():
            if key.startswith(self.type):
                fmt = key.replace(self.type, '', 1)
                setattr(self, self.FRIENDLY.get(fmt.lower(), fmt), Asset(self.type, state=self._state, data={}))

        if self.url is None:
            self.url = getattr(self, 'large', getattr(self, 'medium', getattr(self, 'small', getattr(self, 'png', getattr(self, 'webp', self))))).url

    def __str__(self):
        return self.url

    def __bool__(self):
        return self.url is not None

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return self.url is not None and other.url is not None and self.url == other.url

    async def read(self):
        response = await self._state.get(self.url)
        return await response.read()
