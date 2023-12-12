import inspect
import functools
import threading
from typing import Optional, Callable, Union

from mcdreforged.api.decorator import FunctionThread
from mcdreforged.api.rtext import RTextBase, RTextMCDRTranslation

from where_is.constants import psi, DEBUG

MessageText: type = Union[str, RTextBase]
TRANSLATION_KEY_PREFIX = psi.get_self_metadata().id + '.'


# Utilities
def rtr(translation_key: str, *args, with_prefix: bool = True, **kwargs) -> RTextMCDRTranslation:
    if with_prefix and not translation_key.startswith(TRANSLATION_KEY_PREFIX):
        translation_key = f"{TRANSLATION_KEY_PREFIX}{translation_key}"
    return RTextMCDRTranslation(translation_key, *args, **kwargs).set_translator(ntr)


def debug(msg: Union[str, RTextBase]):
    psi.logger.debug(msg, no_check=DEBUG)


def ntr(
        translation_key: str, *args, language: Optional[str] = None, _mcdr_tr_language: Optional[str] = None,
        allow_failure: bool = True, _default_fallback: Optional[MessageText] = None, log_error_message: bool = True, **kwargs
) -> MessageText:
    if language is not None and _mcdr_tr_language is None:
        _mcdr_tr_language = language
    try:
        return psi.tr(
            translation_key, *args, language=_mcdr_tr_language,
            _mcdr_tr_language=_mcdr_tr_language, allow_failure=False, **kwargs
        )
    except (KeyError, ValueError):
        fallback_language = psi.get_mcdr_language()
        try:
            if fallback_language == 'en_us':
                raise KeyError(translation_key)
            return psi.tr(
                translation_key, *args, _mcdr_tr_language='en_us',
                language='en_us', allow_failure=False, **kwargs
            )
        except (KeyError, ValueError):
            languages = []
            for item in (_mcdr_tr_language, fallback_language, 'en_us'):
                if item not in languages:
                    languages.append(item)
            languages = ', '.join(languages)
            if allow_failure:
                if log_error_message:
                    psi.logger.error(f'Error translate text "{translation_key}" to language {languages}')
                if _default_fallback is None:
                    return translation_key
                return _default_fallback
            else:
                raise KeyError(f'Translation key "{translation_key}" not found with language {languages}')


def dim_tr(key: str, *args, lang: Optional[str] = None, allow_failure: bool = True, **kwargs):
    try:
        return ntr(key, *args, lang=lang, allow_failure=False, **kwargs)
    except Exception as exc:
        if not allow_failure:
            raise exc
        if key.startswith('where_is.dim.'):
            return key[13:]
        else:
            return key


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
    return to_camel_case(psi.get_self_metadata().name, divider=' ') + '_'


def named_thread(arg: Optional[Union[str, Callable]] = None) -> Callable:
    def wrapper(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            def try_func():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    psi.logger.exception('Error running thread {}'.format(threading.current_thread().name), exc_info=e)

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
