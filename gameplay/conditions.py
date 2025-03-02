from __future__ import annotations
from system.saving import SaveAble


class Conditions(SaveAble):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
