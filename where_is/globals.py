from mcdreforged.api.all import *
from typing import Union, Optional

gl_server = ServerInterface.get_instance().as_plugin_server_interface()
DEBUG = True


# Utilities
def tr(key: str, *args, **kwargs):
    plugin_id = gl_server.get_self_metadata().id
    return gl_server.rtr(key if key.startswith(plugin_id) else f"{plugin_id}.{key}", *args, **kwargs)


def debug(msg: Union[str, RTextBase]):
    gl_server.logger.debug(msg, no_check=DEBUG)


def ntr(key: str, *args, lang: Optional[str] = None, allow_failure: bool = True, **kwargs):
    self_id = gl_server.get_self_metadata().id
    if not key.startswith(f'{self_id}.'):
        key = f'{self_id}.{key}'
    if lang != 'en_us':
        try:
            return gl_server.tr(key, *args, language=lang, allow_failure=False, **kwargs)
        except (ValueError, KeyError):
            pass
        except Exception as exc:
            raise exc
    return gl_server.tr(key, *args, language='en_us', allow_failure=allow_failure, **kwargs)


def get_default_mappings(lang: str):
    __REQUIRED_DIMENSIONS = 'overworld', 'the_nether', 'the_end'
    ret = {}
    for dim_key in __REQUIRED_DIMENSIONS:
        ret[dim_key] = ntr(f'default_dim.{dim_key}', lang=lang, allow_failure=False)
    return ret


def dtr(key: str, *args, lang: Optional[str] = None, allow_failure: bool = True, **kwargs):
    try:
        return ntr(key, *args, lang=lang, allow_failure=False, **kwargs)
    except Exception as exc:
        if not allow_failure:
            raise exc
        if key.startswith('where_is.dim.'):
            return key[13:]
        else:
            return key
