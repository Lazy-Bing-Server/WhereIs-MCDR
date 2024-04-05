import inspect
import functools
from typing import Optional, Callable, Union, Dict

from mcdreforged.api.decorator import FunctionThread
from mcdreforged.api.rtext import RTextBase, RTextMCDRTranslation

from where_is.constants import psi, DEBUG

MessageText: type = Union[str, RTextBase]
TRANSLATION_KEY_PREFIX = psi.get_self_metadata().id + '.'
Translatable = Union[str, Dict[str, str]]


class PlayerNameString(str):
    @property
    def possessive(self):
        if self.endswith("s"):
            return self + "'"
        else:
            return self + "'s"


# Utilities
def rtr(translation_key: str, *args, _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX, **kwargs) -> RTextMCDRTranslation:
    if not translation_key.startswith(_lb_rtr_prefix):
        translation_key = f"{_lb_rtr_prefix}{translation_key}"
    return RTextMCDRTranslation(translation_key, *args, **kwargs).set_translator(ntr)


def debug(msg: Union[str, RTextBase]):
    psi.logger.debug(msg, no_check=DEBUG)


def ntr(
        translation_key: str,
        *args,
        _mcdr_tr_language: Optional[str] = None,
        _mcdr_tr_allow_failure: bool = True,
        _lb_tr_default_fallback: Optional[MessageText] = None,
        _lb_tr_log_error_message: bool = True,
        **kwargs
) -> MessageText:
    try:
        return psi.tr(
            translation_key,
            *args,
            _mcdr_tr_language=_mcdr_tr_language,
            _mcdr_tr_allow_failure=False,
            **kwargs
        )
    except (KeyError, ValueError):
        fallback_language = psi.get_mcdr_language()
        try:
            if fallback_language == 'en_us':
                raise KeyError(translation_key)
            return psi.tr(
                translation_key, *args,
                _mcdr_tr_language='en_us',
                _mcdr_tr_allow_failure=False,
                **kwargs
            )
        except (KeyError, ValueError):
            languages = []
            for item in (_mcdr_tr_language, fallback_language, 'en_us'):
                if item not in languages and item is not None:
                    languages.append(item)
            languages = ', '.join(languages)
            if _mcdr_tr_allow_failure:
                if _lb_tr_log_error_message:
                    psi.logger.error(f'Error translate text "{translation_key}" to language {languages}')
                if _lb_tr_default_fallback is None:
                    return translation_key
                return _lb_tr_default_fallback
            else:
                raise KeyError(f'Translation key "{translation_key}" not found with language {languages}')


def ktr(
        translation_key: str,
        *args,
        _lb_tr_default_fallback: Optional[MessageText] = None,
        _lb_tr_log_error_message: bool = False,
        _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX,
        **kwargs
) -> RTextMCDRTranslation:
    return rtr(
        translation_key, *args,
        _lb_rtr_prefix=_lb_rtr_prefix,
        _lb_tr_log_error_message=_lb_tr_log_error_message,
        _lb_tr_default_fallback=translation_key if _lb_tr_default_fallback is None else _lb_tr_default_fallback,
        **kwargs
    )


def to_camel_case(string: str, divider: str = ' ', upper: bool = True) -> str:
    word_list = [capitalize(item) for item in string.split(divider)]
    if not upper:
        first_word_char_list = list(word_list[0])
        first_word_char_list[0] = first_word_char_list[0].lower()
        word_list[0] = ''.join(first_word_char_list)
    return ''.join(word_list)


def capitalize(string: str) -> str:
    if len(string) == 0:
        return string
    char_list = list(string)
    char_list[0] = char_list[0].upper()
    return ''.join(char_list)


def get_thread_prefix() -> str:
    return to_camel_case(psi.get_self_metadata().name, divider=' ') + '@'


def get_translatable_rtext(
        serialized_translate: Optional[Translatable],
        *args,
        **kwargs
) -> Optional[MessageText]:
    require_rtext = (
        any(map((lambda item: isinstance(item, RTextBase)), args))
        or
        any(map((lambda item: isinstance(item[1], RTextBase)), kwargs.items()))
    )

    def format_str(fmt: str) -> MessageText:
        if require_rtext:
            return RTextBase.format(fmt, *args, **kwargs)
        return fmt.format(*args, **kwargs)

    if serialized_translate is None:
        return None
    elif isinstance(serialized_translate, dict):
        mapping = serialized_translate.copy()
        for key, value in serialized_translate.items():
            mapping[key] = format_str(value)
        return RTextMCDRTranslation.from_translation_dict(mapping)
    else:
        return format_str(serialized_translate)


def named_thread(arg: Optional[Union[str, Callable]] = None) -> Callable:
    def wrapper(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            def try_func():
                return func(*args, **kwargs)

            prefix = get_thread_prefix()
            thread = FunctionThread(target=try_func, args=[], kwargs={}, name=prefix + thread_name)
            thread.start()
            return thread

        wrap.__signature__ = inspect.signature(func)
        wrap.original = func
        return wrap

    # Directly use @new_thread without ending brackets case, e.g. @new_thread
    if isinstance(arg, Callable):
        thread_name = to_camel_case(arg.__name__, divider="_")
        return wrapper(arg)
    # Use @new_thread with ending brackets case, e.g. @new_thread('A'), @new_thread()
    else:
        thread_name = arg
        return wrapper
