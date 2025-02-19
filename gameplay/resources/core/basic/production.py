from __future__ import annotations
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import _t


class Production(BasicBaseResource):
    def __init__(self, value, *args, **kwargs):
        super().__init__(
            "core.basic.production",
            _t("content.resources.production.name"),
            _t("content.resources.production.description"),
            value,
            *args,
            **kwargs,
        )
