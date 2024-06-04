from mcdreforged.api.all import MCDRPluginEvents

from threading import RLock

from typing import List

from where_is.utils import named_thread, psi, debug
from where_is.config import config


class OnlinePlayers:
    def __init__(self):
        self.__lock = RLock()
        self.__players: List[str] = []
        self.__limit = 0
        self.__enabled = False

    def get_player_list(self, refresh: bool = False):
        with self.__lock:
            if refresh:
                self.__refresh_online_players()
            return self.__players.copy()

    def get_player_limit(self, refresh: bool = False):
        with self.__lock:
            if refresh:
                self.__refresh_online_players()
            return self.__limit

    @named_thread
    def __add_player(self, player: str):
        with self.__lock:
            if self.__enabled and player not in self.__players:
                self.__players.append(player)

    @named_thread
    def __remove_player(self, player: str):
        with self.__lock:
            if self.__enabled and player in self.__players:
                self.__players.remove(player)

    @named_thread
    def __refresh_online_players(self):
        with self.__lock:
            if not psi.is_server_startup():
                return
            api = psi.get_plugin_instance("minecraft_data_api")
            player_tuple = api.get_server_player_list(
                timeout=config.query_timeout
            )
            if player_tuple is not None:
                count, self.__limit, self.__players = player_tuple
                debug(
                    "Player list refreshed: "
                    + ", ".join(self.__players)
                    + f" (max {self.__limit})"
                )
                if count != len(self.__players):
                    psi.logger.warning(
                        "Incorrect player count found while refreshing player list"
                    )

    @named_thread
    def __enable_player_join(self):
        with self.__lock:
            self.__enabled = True
            debug("Player list counting enabled")

    @named_thread
    def __clear_online_players(self):
        with self.__lock:
            self.__limit, self.__players = None, []
            debug("Cleared online player cache")

    def register_event_listeners(self):
        psi.register_event_listener(
            MCDRPluginEvents.PLUGIN_LOADED,
            lambda *args, **kwargs: self.__refresh_online_players(),
        )
        psi.register_event_listener(
            MCDRPluginEvents.SERVER_START,
            lambda *args, **kwargs: self.__enable_player_join(),
        )
        psi.register_event_listener(
            MCDRPluginEvents.PLAYER_JOINED,
            lambda _, player, __: self.__add_player(player),
        )
        psi.register_event_listener(
            MCDRPluginEvents.PLAYER_LEFT, lambda _, player: self.__remove_player(player)
        )
        psi.register_event_listener(
            MCDRPluginEvents.SERVER_STOP,
            lambda *args, **kwargs: self.__clear_online_players(),
        )


online_players = OnlinePlayers()
