from slowapi import Limiter
from slowapi.util import get_remote_address


# identify each caller by their ip address
limiter = Limiter(key_func=get_remote_address)
