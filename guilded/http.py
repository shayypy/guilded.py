from .errors import *

def parse_client_response(response):
    if response.status < 400:
        return None

    response_dict = {
        403: Forbidden,
        404: NotFound
    }

    try:
        error = response_dict[response.status]
    except KeyError:
        error = HTTPException
    
    raise error()
