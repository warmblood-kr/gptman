class PreambleNotFound(Exception):
    'Preamble not found exception'


class RequestTimeout(Exception):
    'Request timeout'


class NoSuchProfile(Exception):
    def __init__(self, profile_name):
        msg = f"Profile section [profile.{profile_name}] not found" if profile_name \
            else 'Default [gptman] section is not found'
        super().__init__(msg)
