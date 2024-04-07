import re
from typing import Optional, Union, List

from mcdreforged.api.all import *
from minecraft_data_api import get_player_info, get_player_dimension

from where_is.config import config
from where_is.constants import psi
from where_is.dimensions import get_dimension, Dimension, LegacyDimension
from where_is.position import Position
from where_is.online_players import online_players
from where_is.utils import rtr, debug, ntr, named_thread, MessageText
from where_is.node import QuotableTextList


PLAYER_LIST = 'player_list'
SUDO_COUNT = 'sudo_count'
ALL_COUNT = 'all_count'
HIGHLIGHT_TIME = 'highlight_time'


def htr(
    translation_key: str,
    *args,
    prefixes: Optional[List[str]] = None,
    suggest_prefix: Optional[str] = None,
    **kwargs,
) -> RTextMCDRTranslation:
    prefixes = prefixes or [""]

    def __get_regex_result(line: str):
        pattern = r"(?<=§7){}[\S ]*?(?=§)"
        for prefix in prefixes:
            result = re.search(pattern.format(prefix), line)
            if result is not None:
                return result
        return None

    def __htr(key: str, *inner_args, **inner_kwargs) -> MessageText:
        nonlocal suggest_prefix
        original = ntr(key, *inner_args, **inner_kwargs)
        processed: List[MessageText] = []
        if not isinstance(original, str):
            return key
        for line in original.splitlines():
            result = __get_regex_result(line)
            if result is not None:
                command = result.group().strip() + " "
                if suggest_prefix is not None:
                    command = suggest_prefix.strip() + " " + command
                processed.append(
                    RText(line)
                    .c(RAction.suggest_command, command)
                    .h(rtr("help.suggest", command))
                )

                debug(f'Rich help line: "{line}"')
                debug(
                    "Suggest prefix: {}".format(
                        f'"{suggest_prefix}"'
                        if isinstance(suggest_prefix, str)
                        else suggest_prefix
                    )
                )
                debug(f'Suggest command: "{command}"')
            else:
                processed.append(line)
        return RTextBase.join("\n", processed)

    return rtr(translation_key, *args, **kwargs).set_translator(__htr)


@named_thread
def where_is(source: CommandSource, context: CommandContext):
    player_list = context.get(PLAYER_LIST, [])
    sudo = context.get(SUDO_COUNT, 0) > 0
    to_all = context.get(ALL_COUNT, 0) > 0
    highlight_time = context.get(HIGHLIGHT_TIME)
    if len(player_list) == 0:
        where_is_help(source, context)
    for player in player_list:
        _where_is(source, player, sudo=sudo, to_all=to_all, highlight_time=highlight_time)


def where_is_help(source: CommandSource, context: CommandContext):
    current_prefix = context.command.split(' ')[0]
    meta = psi.get_self_metadata()
    version = meta.version
    version_str = ".".join([str(n) for n in version.component])
    if version.pre is not None:
        version_str += "-" + str(version.pre)
    source.reply(htr(
        'help.detailed',
        vris=current_prefix,
        here=config.command_prefix.here_prefixes[0],
        name=meta.name,
        ver=version_str,
        prefixes=[current_prefix, config.command_prefix.here_prefixes[0]]
    ))


def _where_is(
        source: CommandSource,
        target_player: str,
        sudo: bool = False,
        to_all: bool = False,
        highlight_time: Optional[int] = None
):
    highlight_time = highlight_time or config.highlight_time.where_is
    debug("Highlight time: {} s".format(highlight_time))
    if not sudo and not config.location_protection.is_allowed(source, target_player):
        source.reply(rtr('err.player_protected').set_color(RColor.red))
        return
    if target_player not in online_players.get_player_list():
        source.reply(rtr('err.not_online', target_player).set_color(RColor.red))
        return
    try:
        coordinate = get_player_pos(target_player, timeout=config.query_timeout)
        dimension = get_dimension(get_player_dimension(target_player, timeout=config.query_timeout))
        rtext = where_is_text(target_player, coordinate, dimension)
    except Exception as exc:
        source.reply(rtr("err.generic", str(exc)).set_color(RColor.red))
        psi.logger.exception('Unexpected exception occurred while querying player location')
        return

    if to_all:
        say(rtext)
        if highlight_time > 0:
            psi.execute(
                f'effect give {target_player} minecraft:glowing {highlight_time} 0 true'
            )
    else:
        source.reply(rtext)


@named_thread
def here(source: PlayerCommandSource, context: Optional[CommandContext] = None):
    highlight_time = config.highlight_time.here
    if context is not None:
        highlight_time = context.get(HIGHLIGHT_TIME, highlight_time)
    if psi.get_plugin_metadata('here') is not None:
        psi.logger.warning(ntr('warn.duplicated_here'))
        return
    try:
        coordinate = get_player_pos(source.player, timeout=config.query_timeout)
        dimension = get_dimension(get_player_dimension(source.player, timeout=config.query_timeout))
        rtext = where_is_text(source.player, coordinate, dimension)
    except Exception as exc:
        source.reply(rtr("err.generic", str(exc)).set_color(RColor.red))
        psi.logger.exception('Unexpected exception occurred while broadcasting player location')
        return

    say(rtext)
    if highlight_time > 0:
        psi.execute(
            f'effect give {source.player} minecraft:glowing {config.highlight_time.here} 0 true'
        )


def coordinate_text(x: float, y: float, z: float, dimension: Dimension):
    coord = RText('[{}, {}, {}]'.format(int(x), int(y), int(z)), dimension.get_coordinate_color())
    if config.click_to_teleport:
        return (
            coord.h(dimension.get_rtext() + rtr('hover.tp') + coord.copy()).
            c(RAction.suggest_command, '/execute in {} run tp {} {} {}'.format(
                dimension.get_reg_key(), int(x), int(y), int(z)))
        )
    else:
        return coord.h(dimension.get_rtext())


def where_is_text(target_player: str, pos: Position, dim: Dimension) -> RTextBase:
    x, y, z = pos.x, pos.y, pos.z

    # basic text: someone @ dimension [x, y, z]
    texts = RTextList(RText(target_player, RColor.yellow), ' @ ', dim.get_rtext(), ' ',
                      coordinate_text(x, y, z, dim))

    if config.display_waypoints.voxelmap:
        texts.append(' ', RText('[+V]', RColor.aqua).h(rtr('hover.voxel')).c(
            RAction.run_command, '/newWaypoint x:{}, y:{}, z:{}, dim:{}'.format(
                int(x), int(y), int(z), dim.get_reg_key()
            )
        ))

    # click event to add waypoint
    if config.display_waypoints.xaeros_minimap:
        command = "xaero_waypoint_add:{}'s Location:{}:{}:{}:{}:6:false:0".format(
            target_player, target_player[0], int(x), int(y), int(z))
        if isinstance(dim, LegacyDimension):
            command += ':Internal_{}_waypoints'.format(dim.get_reg_key().replace('minecraft:', '').strip())
        texts.append(' ', RText('[+X]', RColor.gold).h(rtr('hover.xaero')).c(RAction.run_command, command))

    # coordinate conversion between overworld and nether
    if dim.has_opposite():
        oppo_dim, oppo_pos = dim.get_opposite(pos)
        arrow = RText('->', RColor.gray)
        texts.append(RText.format(
            ' {} {}',
            arrow.copy().h(RText.format('{} {} {}', dim.get_rtext(), arrow, oppo_dim.get_rtext())),
            coordinate_text(oppo_pos.x, oppo_pos.y, oppo_pos.z, oppo_dim)
        ))

    return texts


# Should be run in new thread
def get_player_pos(player: str, *, timeout: Optional[float] = None) -> Position:
    pos = get_player_info(player, 'Pos', timeout=timeout)
    if pos is None:
        raise ValueError('Fail to query the coordinate of player {}'.format(player))
    return Position(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))


def say(text: Union[str, RTextBase]):
    if config.ocd:
        if config.broadcast_to_console:
            psi.broadcast(text)
        else:
            psi.say(text)
    else:
        if config.broadcast_to_console:
            for line in RTextBase.from_any(text).to_colored_text().splitlines():
                psi.logger.info(line)
        # Tell each player separately to apply language preference
        player_list = online_players.get_player_list()
        if len(player_list) >= 1:
            for player in player_list:
                psi.tell(player, text)


def on_user_info(server: PluginServerInterface, info: Info):
    if config.enable_here and config.enable_inline_here:
        source = info.get_command_source()
        if (
            source.has_permission(config.permission_requirements.here)
            and isinstance(source, PlayerCommandSource)
        ):
            args = info.content.split(' ')
            for prefix in config.command_prefix.here_prefixes:
                if prefix in args:
                    here(source)
                    break


def register_commands(server: PluginServerInterface):
    if config.enable_where_is:
        where_is_root = Literal(config.command_prefix.where_is_prefixes).requires(
            config.permission_requirements.query_is_allowed
        ).runs(where_is)
        where_is_root.then(
            QuotableTextList('player', PLAYER_LIST).suggests(
                lambda: online_players.get_player_list()
            ).redirects(where_is_root)
        )
        where_is_root.then(
            CountingLiteral({"-s", "--sudo"}, SUDO_COUNT).requires(
                config.permission_requirements.is_admin
            ).redirects(where_is_root)
        )
        where_is_root.then(
            CountingLiteral({"-a", "--all"}, ALL_COUNT).requires(
                config.permission_requirements.is_admin
            ).redirects(where_is_root)
        )
        where_is_root.then(
            Literal({"-h", "--highlight"}).then(
                Integer(HIGHLIGHT_TIME).redirects(where_is_root)
            )
        )
        server.register_command(where_is_root)

    if config.enable_here and not config.enable_inline_here:
        here_root = Literal(config.command_prefix.here_prefixes).requires(
            config.permission_requirements.broadcast_is_allowed,
            lambda: rtr('err.perm_denied')
        ).runs(here)
        here_root.then(
            Literal('highlight').then(
                Integer(HIGHLIGHT_TIME).redirects(here_root)
            )
        )
        server.register_command(here_root)


def register_help_messages(server: PluginServerInterface):
    if config.enable_where_is:
        for p in config.command_prefix.where_is_prefixes:
            server.register_help_message(p, server.get_self_metadata().description,
                                         permission=config.permission_requirements.where_is)
    if config.enable_here:
        for p in config.command_prefix.here_prefixes:
            server.register_help_message(p, server.get_self_metadata().description,
                                         permission=config.permission_requirements.here)


def register_customized_translations(server: PluginServerInterface):
    for lang, mappings in config.custom_dimension_name.items():
        server.register_translation(lang, {'where_is': {'dim': config.custom_dimension_name[lang]}})
    config.location_protection.register_tr(server)


def on_load(server: PluginServerInterface, prev_modules):
    online_players.register_event_listeners()
    register_help_messages(server)
    register_customized_translations(server)
    register_commands(server)
    for pre in config.command_prefix.here_prefixes:
        server.register_help_message(pre, rtr('help.here'))
    for pre in config.command_prefix.where_is_prefixes:
        server.register_help_message(pre, rtr('help.vris'))
