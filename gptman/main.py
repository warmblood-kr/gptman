import os
import openai
import logging
import tomllib

from enum import Enum

from gptman import exceptions as exc

logger = logging.getLogger('gptman')


class Backend(Enum):
    openai = 'openai'
    azure = 'azure'


def read_settings(candidates=None):
    settings_path_candidates = candidates or [
        'gptman.toml',
        os.path.expanduser('~/.gptman.toml')
    ]

    for path in settings_path_candidates:
        if not os.path.isfile(path):
            continue

        logging.getLogger(__name__).info('Found settings file at %s', path)
        with open(path, "rb") as f:
            return tomllib.load(f)


def get_client(settings=None, profile=None):
    settings = settings or read_settings()

    _profile = profile if profile else os.getenv('GPTMAN_PROFILE') or None

    if _profile:
        logger.info('Use profile [profile.%s]', _profile)
    else:
        logger.info('Use default profile [gptman]')

    try:
        profile_settings = settings.get('profile', {})[_profile] if _profile \
            else settings['gptman']
    except KeyError as ex:
        key = ex.args[0]
        profile_name = key if key != 'gptman' else None
        raise exc.NoSuchProfile(profile_name)

    backend = Backend[profile_settings.get('backend', 'openai')]

    kwargs = {'api_key': profile_settings['api_key']}

    if backend == Backend.openai:
        client_class = openai.OpenAI
    elif backend == Backend.azure:
        client_class = openai.lib.azure.AzureOpenAI
        kwargs['azure_endpoint'] = profile_settings['azure_endpoint']
        kwargs['api_version'] = profile_settings['api_version']
        if 'azure_deployment' in profile_settings:
            kwargs['azure_deployment'] = profile_settings['azure_deployment']

    return client_class(**kwargs)


