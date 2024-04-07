from mcdreforged.api.all import QuotableText, CommandContext, ParseResult

from typing import Iterable


class QuotableTextList(QuotableText):
    def __init__(self, name: str or Iterable[str], list_key: str):
        super().__init__(name)
        self.__list_key = list_key

    def get_list_key(self):
        return self.__list_key

    def _on_visited(self, context: CommandContext, parse_result: "ParseResult"):
        context[self.__list_key] = context.get(self.__list_key, []) + [parse_result.value]
