from mcdreforged.api.types import ServerInterface

OVERWORLD_SHORT = "overworld"
OVERWORLD = f'minecraft:{OVERWORLD_SHORT}'
NETHER_SHORT = "the_nether"
NETHER = f'minecraft:{NETHER_SHORT}'
END_SHORT = "the_end"
END = f'minecraft:{END_SHORT}'
REG_TO_ID = {
    OVERWORLD: 0,
    NETHER: -1,
    END: 1
}
ID_TO_REG = dict([(v, k) for k, v in REG_TO_ID.items()])

psi = ServerInterface.get_instance().as_plugin_server_interface()
DEBUG = False
