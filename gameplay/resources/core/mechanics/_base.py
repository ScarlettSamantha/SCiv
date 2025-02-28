from __future__ import annotations
from gameplay.resource import BaseResource


class MechanicBaseResource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BaseGreatMechanicResource(MechanicBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
