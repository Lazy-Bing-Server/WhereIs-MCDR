from mcdreforged.api.all import *
from typing import Callable, Any
from where_is.globals import gl_server
from where_is.config import config


def tr(key: str, *args, **kwargs):
    plugin_id = gl_server.get_self_metadata().id
    return gl_server.rtr(key if key.startswith(plugin_id) else f"{plugin_id}.{key}", *args, **kwargs)


@new_thread('WhereIs_GetPlayerInfo')
def __get_data(func: Callable, target_player: str):
    try:
        return func(target_player, timeout=config.query_timeout)
    except ValueError as exc:
        gl_server.logger.error(str(exc))
        return exc


def get_data(func: Callable[[str], Any], target_player: str):
    return __get_data(func, target_player).get_return_value(block=True)
