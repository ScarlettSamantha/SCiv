from __future__ import annotations
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import _t


class Culture(BasicBaseResource):
    def __init__(self, value, *args, **kwargs):
        super().__init__(
            "core.basic.culture",
            _t("content.resources.culture.name"),
            _t("content.resources.culture.description"),
            value,
            *args,
            **kwargs,
        )
