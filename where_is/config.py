from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import CommandSource, PlayerCommandSource
from enum import Enum
from typing import List, Union, Dict

from where_is.globals import gl_server


class PermissionReq(Serializable):
    where_is: int = 1
    admin: int = 3

    def is_allowed(self, source: CommandSource):
        return source.has_permission(self.where_is)

    def is_admin(self, source: CommandSource):
        return source.has_permission(self.admin)


class DisplayWaypoints(Serializable):
    voxelmap: bool = True
    xaeros_minimap: bool = True


class LocationProtection(Serializable):
    enable_whitelist: bool = False
    enable_blacklist: bool = True
    whitelist: List[str] = []
    blacklist: List[str] = []
    protected_text: Dict[str, str] = {
        'en_us': 'He/She\'s in your heart!',
        'zh_cn': 'Ta在你心里!'
    }

    def is_allowed(self, source: CommandSource, target: str):
        if source.is_console:
            return True
        elif isinstance(source, PlayerCommandSource):
            if self.enable_whitelist and target not in self.whitelist:
                return False
            if self.enable_blacklist and target in self.blacklist:
                return False
            return True
        else:
            return False

    def register_tr(self):
        for lang, value in self.protected_text.items():
            gl_server.register_translation(lang, {'where_is.err.player_protected': value})


class TranslationMode(Enum):
    mcdr = True
    minecraft = False


class Config(Serializable):
    command_prefix: Union[List[str], str] = ['!!vris', '!!whereis']
    permission_requirements: PermissionReq = PermissionReq.get_default()
    highlight_time: int = 0
    display_waypoints: DisplayWaypoints = DisplayWaypoints.get_default()
    query_timeout: int = 3
    click_to_teleport: bool = True
    location_protection: LocationProtection = LocationProtection.get_default()
    dimension_translation_mode: TranslationMode = TranslationMode.minecraft

    @classmethod
    def load(cls) -> 'Config':
        cfg = gl_server.load_config_simple(target_class=cls)
        cfg.location_protection.register_tr()
        return cfg

    @property
    def translate_dim_with_mcdr(self):
        return self.dimension_translation_mode.value


config = Config.load()
