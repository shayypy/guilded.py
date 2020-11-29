class GuildedException(Exception):
    """Base exception class for guilded.py
    Ideally speaking, this could be caught to handle any exceptions thrown from this library.
    """
    pass

class BotException(GuildedException):
    """Exception that's thrown when an operation in the :class:`Bot` fails.
    These are usually for exceptions that happened due to user input.
    """
    pass

class CommandException(GuildedException):
	'''Base exception thrown when there's a problem running a command. Usually
	due to user error.'''
	pass

class Forbidden(GuildedException):
    '''Raised when attempting to execute something you are not properly authenticated to do.'''
    pass

class NotFound(GuildedException):
    pass

class HTTPException(GuildedException):
    '''Generic exception raised when a request to Guilded fails.'''
    pass