from mcdreforged.api.all import *
from enum import Enum
from typing import List, Union, Dict, Optional, Any

from where_is.utils import ntr
from where_is.constants import psi, OVERWORLD_SHORT, NETHER_SHORT, END_SHORT, REG_TO_ID, VOXELMAP, XAEROS_MINIMAP


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

    def register_tr(self, server: PluginServerInterface):
        for lang, value in self.protected_text.items():
            server.register_translation(lang, {'where_is.err.player_protected': value})


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


class HighlightTimePreference(Serializable):
    where_is: int = 0
    here: int = 15


class CustomClickableComponent(Serializable):
    enabled: bool = True
    display_text: Union[str, Dict[str, str]] = '[+V]'
    action: str = 'suggest_command'
    click_value: Optional[str] = None
    hover_text: Optional[Union[str, Dict[str, str]]] = None

    def get_display_text(self, *args, **kwargs):
        if isinstance(self.display_text, dict):
            return RTextMCDRTranslation.from_translation_dict(
                translation_dict=self.display_text
            )


class Config(Serializable):
    enable_here: bool = True
    enable_where_is: bool = True
    enable_inline_here: bool = False
    command_prefix: CommandPrefix = CommandPrefix.get_default()
    broadcast_to_console: bool = True
    permission_requirements: PermissionReq = PermissionReq.get_default()
    highlight_time: HighlightTimePreference = HighlightTimePreference.get_default()
    display_waypoints: DisplayWaypoints
    custom_clickable_components: Optional[Dict[str, CustomClickableComponent]] = {
        VOXELMAP: CustomClickableComponent(
            enabled=True,
            display_text='§b[+V]§r',
            click_value='/newWaypoint x:{x}, y:{y}, z:{z}, dim:{dim}',
            action='run_command',
            hover_text={
                'zh_cn': "§bVoxelmap§r: 点此以高亮坐标点, 或者 Ctrl 点击添加路径点",
                'en_us': "§bVoxelmap§r: Click to highlight the location, or Ctrl-Click to add waypoint"
            }
        ),
        XAEROS_MINIMAP: CustomClickableComponent(
            enabled=True,
            display_text='§6[+X]§r',
            click_value="xaero_waypoint_add:{player}'s Location:{player[0]}:{x}:{y}:{z}:6:false:0{dim.xaero_suffix}",
            action='run_command',
            hover_text={
                'zh_cn': "§6Xaeros Minimap§r: 点击添加路径点",
                'en_us': "§6Xaeros Minimap§r: Click to add waypoint"
            }
        )
    }
    query_timeout: int = 3
    click_to_teleport: bool = True
    location_protection: LocationProtection = LocationProtection.get_default()
    dimension_translation_mode: TranslationMode = TranslationMode.mcdr
    custom_dimension_name: Dict[str, Dict[str, str]] = {
        "en_us": {
            OVERWORLD_SHORT: "Overworld",
            NETHER_SHORT: "Nether",
            END_SHORT: "The End"
        },
        "zh_cn": {
            OVERWORLD_SHORT: "主世界",
            NETHER_SHORT: "下界",
            END_SHORT: "末地"
        }
    }
    custom_vanilla_translation_key: Dict[str, str] = {
        OVERWORLD_SHORT: 'createWorld.customize.preset.overworld',
        NETHER_SHORT: 'advancements.nether.root.title',
        END_SHORT: 'advancements.end.root.title'
    }
    # Enable this option will result in invalid MCDR language preference while calling "!!here"
    # But enable this may relieve the emotion of code OCD patients xD
    here_use_broadcast: bool

    def get(self, key: str, default: Any = None):
        if key not in self.get_field_annotations().keys():
            return default
        return getattr(self, key, default)

    @classmethod
    def load(cls) -> 'Config':
        cfg: 'Config' = psi.load_config_simple(target_class=cls)
        if cfg.get('display_waypoints') is not None:
            if VOXELMAP in cfg.custom_clickable_components.keys():
                cfg.custom_clickable_components[VOXELMAP].enabled = cfg.display_waypoints.voxelmap
            if XAEROS_MINIMAP in cfg.custom_clickable_components.keys():
                cfg.custom_clickable_components[XAEROS_MINIMAP].enabled = cfg.display_waypoints.xaeros_minimap
            del cfg.display_waypoints
            psi.save_config_simple(cfg)
            psi.logger.info('Removed deprecated config item: display_waypoints')

        for lang, mappings in cfg.custom_dimension_name.copy().items():
            for key, value in mappings.copy().items():
                cfg.custom_dimension_name[lang][key] = value.strip()
                if cfg.custom_dimension_name[lang][key] == '':
                    del cfg.custom_dimension_name[lang][key]

        requires_save = False
        for lang, mappings in cfg.custom_dimension_name.copy().items():
            missing = []
            for key, value in cls.get_default().custom_dimension_name[lang].items():
                if key not in mappings.keys():
                    cfg.custom_dimension_name[lang][key] = value
                    requires_save = True
                    missing.append(key)
            if len(missing) > 0:
                psi.logger.info(ntr('cfg.vanilla_dim_missed', lang, ', '.join(missing)))

        missing = []
        for key, value in cls.get_default().custom_vanilla_translation_key.items():
            if key not in cfg.custom_vanilla_translation_key.keys():
                cfg.custom_vanilla_translation_key[key] = value
                requires_save = True
                missing.append(key)
        if len(missing) > 0:
            psi.logger.info(ntr('cfg.dim_key_missed', ', '.join(missing)))

        if requires_save:
            psi.save_config_simple(cfg)
        return cfg

    @property
    def translate_dim_with_mcdr(self):
        return self.dimension_translation_mode.value

    def get_translation_key_mappings(self):
        ret = {}
        for key, value in self.custom_vanilla_translation_key.items():
            id_ = REG_TO_ID.get(f"minecraft:{key}")
            if id_ is not None:
                ret[id_] = value
            else:
                ret[key] = value
        return ret

    @property
    def ocd(self):
        return self.get('here_use_broadcast', False)


config = Config.load()
