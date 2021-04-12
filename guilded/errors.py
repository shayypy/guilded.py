class GuildedException(Exception):
    '''Base class for all guilded.py exceptions.'''
    pass

class ClientException(GuildedException):
    pass

class HTTPException(GuildedException):
    '''A non-ok response from Guilded was returned whilst performing an HTTP request.'''
    pass

class BadRequest(HTTPException):
    '''400'''
    pass

class Forbidden(HTTPException):
    '''403'''
    pass

class NotFound(HTTPException):
    '''404'''
    pass

class TooManyRequests(HTTPException):
    '''429'''
    pass

class GuildedServerError(HTTPException):
    '''500'''
    pass

error_mapping = {
    400: BadRequest,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
    500: GuildedServerError
}
