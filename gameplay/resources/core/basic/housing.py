from __future__ import annotations
from gameplay.resources.core.basic._base import BasicBaseResource
from managers.i18n import _t


class Housing(BasicBaseResource):
    def __init__(self, value, *args, **kwargs):
        super().__init__(
            "core.basic.housing",
            _t("content.resources.housing.name"),
            _t("content.resources.housing.description"),
            value,
            *args,
            **kwargs,
        )
