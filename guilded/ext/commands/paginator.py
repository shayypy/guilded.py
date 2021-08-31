
class Paginator:
    """A class that aids in paginating code blocks for Discord messages.

    .. container:: operations

        .. describe:: len(x)

            Returns the total number of characters in the paginator.

    Attributes
    -----------
    prefix: :class:`str`
        The prefix inserted to every page. e.g. three backticks.
    suffix: :class:`str`
        The suffix appended at the end of every page. e.g. three backticks.
    max_size: :class:`int`
        The maximum amount of codepoints allowed in a page.
    linesep: :class:`str`
        The character string inserted between lines. e.g. a newline character.
    """

    def __init__(self, prefix='```', suffix='```', max_size=2000, linesep='\n'):
        self.prefix = prefix
        self.suffix = suffix
        self.max_size = max_size
        self.linesep = linesep
        self.clear()

    def clear(self):
        """Clears the paginator to have no pages."""
        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len  # prefix + newline
        else:
            self._current_page = []
            self._count = 0
        self._pages = []

    @property
    def _prefix_len(self):
        return len(self.prefix) if self.prefix else 0

    @property
    def _suffix_len(self):
        return len(self.suffix) if self.suffix else 0

    @property
    def _linesep_len(self):
        return len(self.linesep)

    def add_line(self, line='', *, empty=False):
        """Adds a line to the current page.

        If the line exceeds the :attr:`max_size` then an exception
        is raised.

        Parameters
        -----------
        line: :class:`str`
            The line to add.
        empty: :class:`bool`
            Indicates if another empty line should be added.

        Raises
        ------
        RuntimeError
            The line was too big for the current :attr:`max_size`.
        """
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            raise RuntimeError(f'Line exceeds maximum page size {max_page_size}')

        if self._count + len(line) + self._linesep_len > self.max_size - self._suffix_len:
            self.close_page()

        self._count += len(line) + self._linesep_len
        self._current_page.append(line)

        if empty:
            self._current_page.append('')
            self._count += self._linesep_len

    def close_page(self):
        """Prematurely terminate a page."""
        if self.suffix is not None:
            self._current_page.append(self.suffix)
        self._pages.append(self.linesep.join(self._current_page))

        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len  # prefix + linesep
        else:
            self._current_page = []
            self._count = 0

    def __len__(self):
        total = sum(len(p) for p in self._pages)
        return total + self._count

    @property
    def pages(self):
        """List[:class:`str`]: Returns the rendered list of pages."""
        # we have more than just the prefix in our current page
        if len(self._current_page) > (0 if self.prefix is None else 1):
            self.close_page()
        return self._pages

    def __repr__(self):
        fmt = '<Paginator prefix: {0.prefix!r} suffix: {0.suffix!r} linesep: {0.linesep!r} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)
