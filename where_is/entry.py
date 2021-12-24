from mcdreforged.api.all import *
from minecraft_data_api import get_player_coordinate, get_player_dimension, Coordinate

from where_is.dimensions import get_dimension, Dimension, LegacyDimension
from where_is.config import config
from where_is.util import tr, get_data


@new_thread('WhereIs_Main')
def where_is(source: CommandSource, target_player: str, parameter: str = '-'):
    para_list = list(parameter[1:])
    if 's' not in para_list and not config.location_protection.is_allowed(source, target_player):
        source.reply(tr('err.player_protected').set_color(RColor.red))
        return
    coordinate = get_data(get_player_coordinate, target_player)
    if isinstance(coordinate, Exception):
        source.reply(tr("err", str(coordinate)).set_color(RColor.red))
        raise coordinate
    dimension = get_data(get_player_dimension, target_player)
    if isinstance(dimension, Exception):
        source.reply(tr("err", str(dimension)).set_color(RColor.red))
        raise dimension
    dimension = get_dimension(dimension)

    rtext = where_is_text(target_player, coordinate, dimension)

    if 'a' in para_list:
        source.get_server().broadcast(rtext)
        if config.highlight_time > 0:
            source.get_server().execute('effect give {} minecraft:glowing {} 0 true'.format(
                target_player, config.highlight_time))
    else:
        source.reply(rtext)


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
            coord.h(dimension.get_rtext() + tr('hover.tp') + coord.copy()).
            c(RAction.suggest_command, '/execute in {} run tp {} {} {}'.format(
                dimension.get_reg_key(), int(x), int(y), int(z)))
        )
    else:
        return coord.h(dimension.get_rtext())


def where_is_text(target_player: str, pos: Coordinate, dim: Dimension) -> RTextBase:
    """
    Main text converter from TISUnion/Here(http://github.com/TISUnion/Here)
    Licensed under GNU General Public License v3.0
    :param target_player: Target player name string
    :param pos: Coordinate object
    :param dim: Dimension object
    :return: Main RText
    """
    x, y, z = pos.x, pos.y, pos.z

    # basic text: someone @ dimension [x, y, z]
    texts = RTextList(RText(target_player, RColor.yellow), ' @ ', dim.get_rtext(), ' ',
                      coordinate_text(x, y, z, dim))

    if config.display_waypoints.voxelmap:
        texts.append(' ', RText('[+V]', RColor.aqua).h(tr('hover.voxel')).c(
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
        texts.append(' ', RText('[+X]', RColor.gold).h(tr('hover.xaero')).c(RAction.run_command, command))

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


def register_commands(server: PluginServerInterface):
    server.register_command(
        Literal(config.command_prefix).then(
            QuotableText("player").requires(
                config.permission_requirements.is_allowed
            ).runs(
                lambda src, ctx: where_is(src, ctx['player'])).then(
                QuotableText('parameter').requires(
                    config.permission_requirements.is_admin
                ).requires(
                    lambda src, ctx: ctx['parameter'].startswith('-')
                ).runs(
                    lambda src, ctx: where_is(src, ctx['player'], ctx['parameter'])
                )
            )
        )
    )


def on_load(server: PluginServerInterface, prev_modules):
    if isinstance(config.command_prefix, list):
        for p in config.command_prefix:
            server.register_help_message(p, server.get_self_metadata().description,
                                         permission=config.permission_requirements.where_is)
    register_commands(server)
