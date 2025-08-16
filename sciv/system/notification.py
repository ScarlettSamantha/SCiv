from typing import Any, Dict, List

from gameplay.notification import Notifications


class Notification:
    notification_instance: Notifications = Notifications()

    @classmethod
    def initialize(cls) -> None:
        cls.notification_instance.initialize()

    @classmethod
    def reset(cls) -> None:
        cls.notification_instance.reset()

    @classmethod
    def dump(cls) -> Dict[str, List[Dict[str, Any]]]:
        return cls.notification_instance.dump()

    @classmethod
    def load(cls, state: Dict[str, Any]) -> None:
        cls.notification_instance.load(state)

    @classmethod
    def check(cls) -> None:
        cls.notification_instance.check_non_persistent_notifications()
        cls.notification_instance.check_persistent_notifications()
