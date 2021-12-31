from mcdreforged.api.all import *
from typing import Union

gl_server = ServerInterface.get_instance().as_plugin_server_interface()
DEBUG = True


def tr(key: str, *args, **kwargs):
    plugin_id = gl_server.get_self_metadata().id
    return gl_server.rtr(key if key.startswith(plugin_id) else f"{plugin_id}.{key}", *args, **kwargs)


def debug(msg: Union[str, RTextBase]):
    gl_server.logger.debug(msg, no_check=DEBUG)
