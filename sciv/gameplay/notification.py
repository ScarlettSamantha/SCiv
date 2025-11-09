from pathlib import Path
from typing import Any, Dict, List, Type

from gameplay.condition import Conditions
from helpers.paths import PathsHelper


class Notifications:
    NOTIFICATIONS_FOLDER: Path = PathsHelper.get_gameplay_dir() / "notifications"
    NOTIFICATIONS_PERSISTENT: Path = NOTIFICATIONS_FOLDER / "persistent"
    NOTIFICATIONS_NON_PERSISTENT: Path = NOTIFICATIONS_FOLDER / "transient"

    registered_notifications: List[Type["Notification"]] = []
    registered_persistent_notifications: List[Type["Notification"]] = []

    active_notifications: List["Notification"] = []
    active_persistent_notifications: List["Notification"] = []

    _initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        from system.pyload import PyLoad

        path_persistent = str(cls.NOTIFICATIONS_PERSISTENT.resolve())
        path_non_persistent = str(cls.NOTIFICATIONS_NON_PERSISTENT.resolve())

        persistent_notifications: Dict[str, Type[Notification]] = PyLoad.load_classes(
            path_persistent, package="gameplay.notifications.persistent"
        )
        non_persistent_notifications: Dict[str, Type[Notification]] = PyLoad.load_classes(
            path_non_persistent, package="gameplay.notifications.transient"
        )

        for notification in persistent_notifications.values():
            cls.register_notification(notification)

        for notification in non_persistent_notifications.values():
            cls.register_notification(notification)

        cls.check_persistent_notifications()
        cls.check_non_persistent_notifications()

        cls._initialized = True

    @classmethod
    def reset(cls) -> None:
        cls.registered_notifications.clear()
        cls.registered_persistent_notifications.clear()
        cls.active_notifications.clear()
        cls.active_persistent_notifications.clear()

        cls._initialized = False

    @classmethod
    def register_notification(cls, notification: Type["Notification"]) -> None:
        cls.registered_notifications.append(notification)
        if notification.is_persistent():
            cls.registered_persistent_notifications.append(notification)

    @classmethod
    def get_registered_notifications(cls) -> List[Type["Notification"]]:
        return cls.registered_notifications

    @classmethod
    def get_registered_persistent_notifications(cls) -> List[Type["Notification"]]:
        return cls.registered_persistent_notifications

    @classmethod
    def get_notification_by_key(cls, key: str) -> Type["Notification"] | None:
        for notification in cls.registered_notifications:
            if notification.get_key() == key:
                return notification
        return None

    @classmethod
    def is_notification_active(cls, notification: Type["Notification"]) -> bool:
        for active_notification in cls.active_notifications:
            if type(active_notification) == notification and active_notification.get_key() == notification.get_key():
                return True
        return False

    @classmethod
    def is_persistent_notification_active(cls, notification: Type["Notification"]) -> bool:
        for active_notification in cls.active_persistent_notifications:
            if type(active_notification) == notification and active_notification.get_key() == notification.get_key():
                return True
        return False

    @classmethod
    def get_active_persistent_notification_by_key(cls, key: str) -> "Notification | None":
        for notification in cls.active_persistent_notifications:
            if notification.get_key() == key:
                return notification
        return None

    @classmethod
    def check_persistent_notifications(cls) -> None:
        for notification in cls.registered_persistent_notifications:
            if cls.is_persistent_notification_active(notification):
                if not notification.conditions_met():
                    instance = cls.get_active_persistent_notification_by_key(notification.get_key())
                    if instance:
                        cls.dismiss_notification(instance)
            else:
                if notification.conditions_met():
                    instance = notification()
                    instance.on_trigger()
                    cls.active_persistent_notifications.append(instance)

    @classmethod
    def check_non_persistent_notifications(cls) -> None:
        for notification in cls.registered_notifications:
            if not notification.is_persistent() and notification.conditions_met():
                instance = notification()
                instance.on_trigger()
                cls.active_notifications.append(instance)

    @classmethod
    def dismiss_notification(cls, notification: "Notification") -> None:
        if notification in cls.active_notifications:
            cls.active_notifications.remove(notification)
            notification.on_dismiss()

        if notification in cls.active_persistent_notifications:
            cls.active_persistent_notifications.remove(notification)
            notification.on_dismiss()

    @classmethod
    def dump(cls) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "active_notifications": [n.dump() for n in cls.active_notifications],
            "active_persistent_notifications": [n.dump() for n in cls.active_persistent_notifications],
        }

    @classmethod
    def load(cls, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        for notification_state in state.get("active_notifications", []):
            notification_cls: Type[Notification] = EntityManager.dynamic_import(notification_state["_cls"])
            assert issubclass(notification_cls, Notification), "Loaded class is not a Notification"
            notification: Notification = notification_cls.load(notification_state)
            cls.active_notifications.append(notification)

        for notification_state in state.get("active_persistent_notifications", []):
            notification_cls: Type[Notification] = EntityManager.dynamic_import(notification_state["_cls"])
            assert issubclass(notification_cls, Notification), "Loaded class is not a Notification"
            notification: Notification = notification_cls.load(notification_state)
            cls.active_persistent_notifications.append(notification)


class Notification:
    key: str = "NOTIFICATION"
    persistent: bool = False
    conditions: Conditions = Conditions()

    @classmethod
    def get_key(cls) -> str:
        return cls.key

    @classmethod
    def is_persistent(cls) -> bool:
        return cls.persistent

    @classmethod
    def conditions_met(cls) -> bool:
        if cls.on_check() is True:
            return True
        else:
            return cls.conditions.are_met()

    def on_trigger(self) -> None:
        pass

    def on_dismiss(self) -> None:
        pass

    @classmethod
    def on_check(cls) -> bool: ...

    @classmethod
    def dump(cls) -> Dict[str, Any]:
        return {"key": cls.get_key(), "cls_ref": f"{cls.__module__}.{cls.__class__.__name__}"}

    @classmethod
    def load(cls, state: Dict[str, Any]) -> "Notification":
        from managers.entity import EntityManager

        notification_cls = EntityManager.dynamic_import(state["_cls"])
        assert issubclass(notification_cls, Notification), "Loaded class is not a Notification"
        notification = notification_cls()
        return notification


class PersistentNotification(Notification):
    persistent: bool = True


class TransientNotification(Notification):
    persistent: bool = False
