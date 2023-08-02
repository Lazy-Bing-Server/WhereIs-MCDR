from mcdreforged.api.rtext import RTextBase
from typing import Union, Optional

from where_is.constants import gl_server, DEBUG


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
