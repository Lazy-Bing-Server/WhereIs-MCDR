from abc import ABC
from typing import Tuple

from mcdreforged.api.rtext import RColor, RTextBase, RTextTranslation
from where_is.config import config
from where_is.constants import OVERWORLD, NETHER, END, REG_TO_ID, ID_TO_REG, OVERWORLD_SHORT, NETHER_SHORT, END_SHORT
from where_is.utils import rtr, dim_tr, debug
from where_is.position import Position

"""
Copied from TISUnion/Here
Original repository: https://github.com/TISUnion/Here

Licensed under GNU General Public License v3.0
"""


class Dimension(ABC):
    def get_id(self) -> str:  # 0
        raise NotImplementedError()

    def get_reg_key(self) -> str:  # minecraft:overworld
        raise NotImplementedError()

    def get_color(self) -> RColor:
        return {
            OVERWORLD: RColor.dark_green,
            NETHER: RColor.dark_red,
            END: RColor.dark_purple
        }.get(self.get_reg_key(), RColor.gray)

    def get_coordinate_color(self) -> RColor:
        return {
            OVERWORLD: RColor.green,
            NETHER: RColor.red,
            END: RColor.light_purple
        }.get(self.get_reg_key(), RColor.white)

    def get_rtext(self) -> RTextBase:
        raise NotImplementedError()

    def has_opposite(self) -> bool:
        raise NotImplementedError()

    def get_opposite(self, pos: Position) -> Tuple['Dimension', Position]:
        raise NotImplementedError()


class LegacyDimension(Dimension):
    def __init__(self, dim_id: int):
        assert isinstance(dim_id, int) and -1 <= dim_id <= 1
        self.dim_id = dim_id

    def get_id(self) -> int:
        return self.dim_id

    def get_reg_key(self) -> str:
        return ID_TO_REG[self.dim_id]

    def get_rtext(self) -> RTextBase:
        if config.translate_dim_with_mcdr:
            return rtr({
                0: f'dim.{OVERWORLD_SHORT}',
                -1: f'dim.{NETHER_SHORT}',
                1: f'dim.{END_SHORT}'
            }[self.dim_id]).set_color(self.get_color())
        return RTextTranslation(config.get_translation_key_mappings()[self.dim_id], color=self.get_color())

    def has_opposite(self) -> bool:
        return self.dim_id in (0, -1)

    def get_opposite(self, pos: Position) -> Tuple['Dimension', Position]:
        # 0 -> -1
        # -1 -> 0
        if self.dim_id == 0:  # overworld
            return LegacyDimension(-1), pos.to_nether()
        elif self.dim_id == -1:  # nether
            return LegacyDimension(0), pos.to_overworld()
        raise RuntimeError('Legacy dimension -1 (the end) does not have opposite dimension')


class CustomDimension(Dimension):
    def __init__(self, reg_key: str):
        self.reg_key = reg_key

    def get_id(self) -> str:
        raise RuntimeError('Custom dimension {} does not have integer id'.format(self.reg_key))

    def get_reg_key(self) -> str:
        return self.reg_key

    def get_rtext(self) -> RTextBase:
        translation_key_mappings = config.get_translation_key_mappings()
        if config.translate_dim_with_mcdr or self.reg_key not in translation_key_mappings:
            return rtr(f"dim.{self.reg_key}").set_translator(dim_tr).set_color(self.get_color())
        else:
            return RTextTranslation(config.get_translation_key_mappings()[self.reg_key], color=self.get_color())

    def has_opposite(self) -> bool:
        return False

    def get_opposite(self, pos: Position) -> Tuple['Dimension', Position]:
        raise RuntimeError('Custom dimension {} does not have opposite dimension'.format(self.reg_key))


def get_dimension(text: str) -> Dimension:
    """
    text can be:
    - int id: 0
    - str registry key: minecraft:overworld
    """
    try:
        return LegacyDimension(int(text))
    except:
        pass
    debug(text)
    if text in REG_TO_ID.keys():
        return LegacyDimension(REG_TO_ID[text])
    return CustomDimension(text)
