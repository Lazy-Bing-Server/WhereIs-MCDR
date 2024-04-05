from typing import Optional, Union

from mcdreforged.api.command import Literal, QuotableText
from mcdreforged.api.rtext import RColor, RTextBase, RText, RAction, RTextList
from mcdreforged.api.types import CommandSource, PlayerCommandSource, Info, PluginServerInterface
from minecraft_data_api import get_player_info, get_player_dimension, get_server_player_list

from where_is.config import config
from where_is.constants import psi
from where_is.dimensions import get_dimension, Dimension, LegacyDimension
from where_is.position import Position
from where_is.utils import rtr, debug, ntr, named_thread, get_translatable_rtext, PlayerNameString


@named_thread
def where_is(source: CommandSource, target_player: str, args: str = '-'):
    para_list = list(args[1:])
    if 's' not in para_list and not config.location_protection.is_allowed(source, target_player):
        source.reply(rtr('err.player_protected').set_color(RColor.red))
        return
    try:
        player_list = get_server_player_list(timeout=config.query_timeout)[2]
        debug(str(player_list))
        if target_player not in tuple([] if player_list is None else player_list):
            source.reply(rtr('err.not_online').set_color(RColor.red))
            return
        coordinate = get_player_pos(target_player, timeout=config.query_timeout)
        dimension = get_dimension(get_player_dimension(target_player, timeout=config.query_timeout))
        rtext = where_is_text(target_player, coordinate, dimension)
    except Exception as exc:
        source.reply(rtr("err.generic", str(exc)).set_color(RColor.red))
        psi.logger.exception('Unexpected exception occurred while querying player location')
        return

    if 'a' in para_list:
        say(rtext)
        if config.highlight_time.where_is > 0:
            psi.execute('effect give {} minecraft:glowing {} 0 true'.format(
                target_player, config.highlight_time.where_is))
    else:
        source.reply(rtext)


@named_thread
def here(source: PlayerCommandSource):
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
    if config.highlight_time.here > 0:
        psi.execute('effect give {} minecraft:glowing {} 0 true'.format(
            source.player, config.highlight_time.here))


def coordinate_text(x: float, y: float, z: float, dimension: Dimension):
    """
    Coordinate text converter from TISUnion/Here(http://github.com/TISUnion/Here)
    Licensed under GNU General Public License v3.0
    :param x: Coordinate on X axis
    :param y: Coordinate on Y axis
    :param z: Coordinate on Z axis
    :param dimension: Converted dimension objects
    :return: RText object of this coordinates
    """
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
    """
    Main text converter from TISUnion/Here(http://github.com/TISUnion/Here)
    Licensed under GNU General Public License v3.0
    :param target_player: Target player name string
    :param pos: Coordinate object
    :param dim: Dimension object
    :return: Main RText
    """
    x, y, z = pos.x, pos.y, pos.z
    target_player_text = PlayerNameString(target_player)

    # basic text: someone @ dimension [x, y, z]
    texts = [
        RText(target_player_text, RColor.yellow),
        '@',
        dim.get_rtext(),
        coordinate_text(x, y, z, dim)]

    if len(config.custom_clickable_components) > 0:
        kwargs = dict(
            player=target_player_text,
            dim=dim, x=x, y=y, z=z
        )
        for item in config.custom_clickable_components.values():
            if not item.enabled:
                continue
            texts.append(
                RText(
                    get_translatable_rtext(item.display_text, **kwargs)
                ).c(
                    RAction[item.action], item.click_value.format(**kwargs)
                ).h(
                    get_translatable_rtext(item.hover_text, **kwargs)
                )
            )

    # coordinate conversion between overworld and nether
    if dim.has_opposite():
        oppo_dim, oppo_pos = dim.get_opposite(pos)
        arrow = RText('->', RColor.gray)
        texts.append(RText.format(
            '{} {}',
            arrow.copy().h(RText.format('{} {} {}', dim.get_rtext(), arrow, oppo_dim.get_rtext())),
            coordinate_text(oppo_pos.x, oppo_pos.y, oppo_pos.z, oppo_dim)
        ))

    return RTextBase.join(' ', texts)


# Should be run in new thread
def get_player_pos(player: str, *, timeout: Optional[float] = None) -> Position:
    pos = get_player_info(player, 'Pos', timeout=timeout)
    if pos is None:
        raise ValueError('Fail to query the coordinate of player {}'.format(player))
    return Position(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))


# Should be run in new thread
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
        current_amount, max_amount, player_list = get_server_player_list(timeout=config.query_timeout)
        if current_amount >= 1:
            for player in player_list:
                psi.tell(player, text)


def on_user_info(server: PluginServerInterface, info: Info):
    if config.enable_here and config.enable_inline_here:
        source = info.get_command_source()
        if source.has_permission(config.permission_requirements.here) and isinstance(source, PlayerCommandSource):
            args = info.content.split(' ')
            for prefix in config.command_prefix.here_prefixes:
                if prefix in args:
                    here(source)
                    break


def is_available_para(string: str):
    arg_list = list(string)
    if arg_list.pop(0) != '-' or len(arg_list) == 0:
        return False
    if 'a' in arg_list:
        arg_list.remove('a')
    if 's' in arg_list:
        arg_list.remove('s')
    if len(arg_list) != 0:
        return False
    return True


def register_commands(server: PluginServerInterface):
    if config.enable_where_is:
        server.register_command(
            Literal(config.command_prefix.where_is_prefixes).then(
                QuotableText("player").requires(
                    config.permission_requirements.query_is_allowed, lambda: rtr('err.perm_denied')
                ).runs(
                    lambda src, ctx: where_is(src, ctx['player'])).then(
                    QuotableText('args').requires(
                        config.permission_requirements.is_admin, lambda: rtr('err.perm_denied')
                    ).requires(
                        lambda src, ctx: is_available_para(ctx['args']), lambda: rtr('err.invalid_args')
                    ).runs(
                        lambda src, ctx: where_is(src, ctx['player'], ctx['args'])
                    )
                )
            )
        )

    if config.enable_here and not config.enable_inline_here:
        server.register_command(
            Literal(config.command_prefix.here_prefixes).requires(
                config.permission_requirements.broadcast_is_allowed, lambda: rtr('err.perm_denied')
            ).runs(lambda src: here(src))
        )


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
    register_help_messages(server)
    register_customized_translations(server)
    register_commands(server)
