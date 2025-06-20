from typing import Tuple

from managers.i18n import T_TranslationOrStrOrNone


class Age:
    key: T_TranslationOrStrOrNone
    name: T_TranslationOrStrOrNone
    description: T_TranslationOrStrOrNone
    color: Tuple[int, int, int, int] | None
