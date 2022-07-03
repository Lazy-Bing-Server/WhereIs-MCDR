from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import CommandSource, PlayerCommandSource
from enum import Enum
from typing import List, Union, Dict

from where_is.globals import gl_server, get_default_mappings, ntr


class PermissionReq(Serializable):
    where_is: int = 1
    here: int = 0
    admin: int = 3

    def query_is_allowed(self, source: CommandSource):
        return source.has_permission(self.where_is)

    def broadcast_is_allowed(self, source: CommandSource):
        return source.has_permission(self.here) and isinstance(source, PlayerCommandSource)

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


class CommandPrefix(Serializable):
    where_is: Union[List[str], str] = ['!!vris', '!!whereis']
    here: Union[List[str], str] = ['!!here']

    @property
    def where_is_prefixes(self) -> List[str]:
        if isinstance(self.where_is, str):
            return [self.where_is]
        return self.where_is

    @property
    def here_prefixes(self) -> List[str]:
        if isinstance(self.here, str):
            return [self.here]
        return self.here


class DimensionTranslationMappings(dict, Serializable):
    overworld: str = 'Overworld'
    the_nether: str = 'Nether'
    the_end: str = 'The End'


class HighlightTimePreference(Serializable):
    where_is: int = 0
    here: int = 15


class Config(Serializable):
    enable_here: bool = True
    enable_where_is: bool = True
    command_prefix: CommandPrefix = CommandPrefix.get_default()
    permission_requirements: PermissionReq = PermissionReq.get_default()
    highlight_time: HighlightTimePreference = HighlightTimePreference.get_default()
    display_waypoints: DisplayWaypoints = DisplayWaypoints.get_default()
    query_timeout: int = 3
    click_to_teleport: bool = True
    location_protection: LocationProtection = LocationProtection.get_default()
    dimension_translation_mode: TranslationMode = TranslationMode.minecraft
    custom_dimension_name: Dict[str, Dict[str, str]] = {}

    @classmethod
    def get_default(cls):
        default = cls.deserialize({})
        for lang in ('en_us', 'zh_cn'):
            default.custom_dimension_name[lang] = get_default_mappings(lang)
        return default

    @classmethod
    def load(cls) -> 'Config':
        cfg = gl_server.load_config_simple(target_class=cls)

        for lang, mappings in cfg.custom_dimension_name.copy().items():
            for key, value in mappings.copy().items():
                cfg.custom_dimension_name[lang][key] = value.strip()
                if cfg.custom_dimension_name[lang][key] == '':
                    del cfg.custom_dimension_name[lang][key]

        requires_save = False
        for lang, mappings in cfg.custom_dimension_name.copy().items():
            missing = []
            for key, value in get_default_mappings(lang).items():
                if key not in mappings.keys():
                    cfg.custom_dimension_name[lang][key] = value
                    requires_save = True
                    missing.append(key)
            if len(missing) > 0:
                gl_server.logger.info(ntr('cfg.vanilla_dim_missed', lang, ', '.join(missing)))
            gl_server.register_translation(lang, {'where_is': {'dim': cfg.custom_dimension_name[lang]}})

        cfg.location_protection.register_tr()

        if requires_save:
            gl_server.save_config_simple(cfg)
        return cfg

    @property
    def translate_dim_with_mcdr(self):
        return self.dimension_translation_mode.value


config = Config.load()
