import io
import json
import pathlib
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Optional, Union

from exceptions.i18n_exception import (
    I18NDecodeException,
    I18NLoadException,
    I18NNotLoadedException,
    I18NTranslationNotFound,
)


class _i18n:
    def __init__(
        self,
        base_path: str | Path | PathLike[Any],
        language: str | None = None,
        auto_load: bool = True,
        manager: Any = None,
    ) -> None:
        self.base_path: str | Path | PathLike[Any] = base_path
        self._data: Dict[str, Dict[Any, Any]] = {}
        self.manager: Any = manager

        self.default_language = "en_EN"
        self.language: str = language if language else self.default_language

        # Initialize the lookup cache as an instance variable
        self._lookup_cache: Dict[str, str] = {}

        if auto_load and self.language_exists(language=self.language):
            self.load_language(language=self.language)

    def clear_cache(self) -> None:
        """Clear the lookup cache."""
        self._lookup_cache.clear()

    def generate_path(self, path: PathLike[Any] | str) -> Path:
        base_path = Path(self.base_path) if not isinstance(self.base_path, Path) else self.base_path
        return base_path / Path(path)

    def language_exists(self, language: str) -> bool:
        path = pathlib.Path(self.generate_path(path=f"{language}.json"))
        return path.exists()

    def get_data(self) -> Dict[str, Dict[Any, Any]]:
        return self._data

    def set_data(self, data: Dict[str, Dict[Any, Any]]) -> None:
        self._data = data
        self.clear_cache()  # Clear cache if underlying data changes

    def load_file(self, path: str) -> None:
        try:
            f = io.open(file=path, mode="r")
        except FileNotFoundError:
            raise I18NLoadException(f"Failed to open {path}")
        try:
            self._data.update(json.loads(f.read()))
        except json.JSONDecodeError:
            raise I18NDecodeException(f"Failed to decode {path}")

    def current_language(self) -> str:
        return self.language

    def set_current_language(self, language: str) -> None:
        self.language = language
        self.clear_cache()  # Clear cache when language changes

    def load_language(self, language: str):
        self.load_file(path=str(self.generate_path(path=f"{language}.json")))
        self.clear_cache()  # Clear cache after loading new language data

    def lookup(
        self,
        key: "str | T_TranslationOrStr",
        default: Any | None = None,
        fail_on_not_found: bool = True,
        formatting_parameters: Optional[Dict[str, Any]] = None,
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        # Check if the key is in the cache
        if isinstance(key, Translation):
            key = str(key)

        def format_result(result: str) -> str:
            if formatting_parameters is not None:
                try:
                    return result.format(**formatting_parameters)
                except KeyError:
                    raise I18NTranslationNotFound(f"String formatting key[{key}] not found")
            return prefix + result + suffix

        if key in self._lookup_cache:
            return format_result(self._lookup_cache[key])

        data = self._data[self.language]
        splits: list[str] = str(key).split(sep=".")
        for i, level in enumerate(splits):
            if level in data:
                data = data[level]
                if i == (len(splits) - 1):
                    return format_result(data)
            else:
                if fail_on_not_found:
                    raise I18NTranslationNotFound(f"Key {key} not found")
                result = key
                self._lookup_cache[key] = result
                if formatting_parameters is not None:
                    result = result.format(**formatting_parameters)
                return prefix + result + suffix
        if default is None and fail_on_not_found:
            raise I18NTranslationNotFound(f"Key {key} not found")
        result = key if default is None else default
        # Cache the result, we do it here as we dont want to store the formatting parameters
        self._lookup_cache[key] = result

        return format_result(result)


i18n: None | _i18n = None


def set_i18n(i18n_instance: _i18n) -> None:
    global i18n
    i18n = i18n_instance


def get_i18n() -> _i18n:
    global i18n
    if i18n is None:
        raise I18NNotLoadedException("I18n not loaded")
    return i18n


class Translation:
    def __init__(
        self, key: str, parameters: Optional[Dict[str, Any]] = None, suffix: str = "", prefix: str = ""
    ) -> None:
        self.key: str = key
        self.formatting_parameters: Optional[Dict[str, Any]] = parameters

    def __repr__(self) -> str:
        self_str: str = str(self) if i18n else "[!unloaded i18n engine!]"
        return f"Translation({self.key}) -> {self_str}"

    def __str__(self) -> str:
        if i18n is None:
            raise I18NNotLoadedException(
                "I18n not loaded, there is probably not an instance of the manager earle enough in your load order."
            )
        try:
            # We want to handle the fail in the translation object so we can handle it on a higher level.
            return i18n.lookup(key=self.key, fail_on_not_found=True, formatting_parameters=self.formatting_parameters)
        except I18NTranslationNotFound:
            return self.key

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: "Translation | object") -> bool:
        if not isinstance(other, Translation):
            return False
        return self.key == other.key

    def __len__(self) -> int:
        """Return the length of the string representation of the translation."""
        return len(self.__str__())


_t = Translation
t_ = Translation
T_TranslationOrStr = Union[Translation, str]
T_TranslationOrStrOrNone = Union[Translation, str, None]
