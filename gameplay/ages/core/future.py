from gameplay.age import Age
from managers.i18n import _t


class Future(Age):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="ancient",
            name=_t("content.ages.core.future.name"),
            description=_t("content.ages.core.future.description"),
            color=(0, 255, 0, 0),
            *args,
            **kwargs,
        )
