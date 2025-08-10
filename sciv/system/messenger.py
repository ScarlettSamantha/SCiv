import heapq
from copy import copy
from datetime import datetime
from typing import Any, Dict, Iterator, List, OrderedDict, Tuple, Type, cast

from kivy.uix.image import Image
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class Message:
    DURATION_DEFAULT: float = 5.0  # Default duration for messages
    DURATION_PERMANENT: float = -1.0  # Permanent messages do not disappear

    def __init__(
        self,
        title: T_TranslationOrStr,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStrOrNone = None,
        duration: float = DURATION_DEFAULT,
        color: tuple[float, ...] = (1.0, 1.0, 1.0, 1.0),
        visible: bool = True,
        is_closable: bool = True,
        is_clickable: bool = False,
        is_blocking: bool = False,
        is_disabled: bool = False,
        on_click_arguments: Dict[Any, Any] = {},
        created_at: float | None = None,
    ):
        self.title: T_TranslationOrStr = title
        self.text: T_TranslationOrStr = text
        self.tooltip: T_TranslationOrStrOrNone = tooltip
        self.duration: float = duration
        self.color: Tuple[float, ...] = color
        self.visible: bool = visible
        self.created_at: float = datetime.now().timestamp() if created_at is None else created_at
        self.is_closable: bool = is_closable
        self.is_blocking: bool = is_blocking
        self.is_clickable: bool = is_clickable
        self.is_disabled: bool = is_disabled
        self.on_click_arguments: Dict[Any, Any] = on_click_arguments

    def register_on_click(self) -> None:
        if self.is_clickable:
            raise NotImplementedError("Subclasses should implement the on_click method.")

    def hide(self) -> None:
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def toggle_visibility(self) -> None:
        self.visible = not self.visible

    def on_click(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Subclasses should implement the on_click method.")

    def execute_click(self, *args: List[Any], **kwargs: Dict[str, Any]) -> Any:
        if not self.is_disabled:
            return self.on_click(*args, **kwargs, **self.on_click_arguments)
        return None

    def __repr__(self) -> str:
        return f"Message(text={self.text}, duration={self.duration}, color={self.color})"

    def get_formatted_text(self) -> str:
        return str(str(self.text).format(**self.on_click_arguments))

    def get_icon(self) -> str | Image | None:
        raise NotImplementedError("Subclasses should implement the get_icon method.")

    def dump(self) -> Dict[str, Any]:
        return {
            "title": str(self.title),
            "text": str(self.text),
            "tooltip": str(self.tooltip),
            "duration": self.duration,
            "color": self.color,
            "visible": self.visible,
            "created_at": self.created_at,
            "is_closable": self.is_closable,
            "is_blocking": self.is_blocking,
            "is_clickable": self.is_clickable,
            "is_disabled": self.is_disabled,
            "on_click_arguments": self.on_click_arguments,
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    def load(self, state: Dict[str, Any]) -> None:
        self.title = state.get("title", "")
        self.text = state.get("text", "")
        self.tooltip = state.get("tooltip", None)
        self.duration = state.get("duration", self.DURATION_DEFAULT)
        self.color = tuple(state.get("color", (1.0, 1.0, 1.0, 1.0)))
        self.visible = state.get("visible", True)
        self.created_at = state.get("created_at", datetime.now().timestamp())
        self.is_closable = state.get("is_closable", True)
        self.is_blocking = state.get("is_blocking", False)
        self.is_clickable = state.get("is_clickable", False)
        self.is_disabled = state.get("is_disabled", False)
        self.on_click_arguments = state.get("on_click_arguments", {})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        message = cls(
            title=data.get("title", ""),
            text=data.get("text", ""),
            tooltip=data.get("tooltip"),
            duration=data.get("duration", cls.DURATION_DEFAULT),
            color=tuple(data.get("color", (1.0, 1.0, 1.0, 1.0))),  # type: ignore
            visible=data.get("visible", True),
            is_closable=data.get("is_closable", True),
            is_blocking=data.get("is_blocking", False),
            is_clickable=data.get("is_clickable", False),
            is_disabled=data.get("is_disabled", False),
        )
        message.register_on_click()
        message.created_at = data.get("created_at", datetime.now().timestamp())
        return message

    @classmethod
    def permanent(
        cls,
        title: T_TranslationOrStr,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStr | None = None,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        icon: str = "",
        is_closable: bool = True,
        is_blocking: bool = False,
    ) -> "Message":
        return cls(
            title=title,
            text=text,
            tooltip=tooltip,
            duration=cls.DURATION_PERMANENT,
            color=color,
            visible=True,
            is_closable=is_closable,
            is_blocking=is_blocking,
        )

    @classmethod
    def temporary(
        cls,
        title: T_TranslationOrStr,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStr | None = None,
        duration: float = DURATION_DEFAULT,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        icon: str = "",
        is_closable: bool = True,
        is_blocking: bool = False,
    ) -> "Message":
        return cls(
            title=title,
            text=text,
            tooltip=tooltip,
            duration=duration,
            color=color,
            visible=True,
            is_closable=is_closable,
            is_blocking=is_blocking,
        )


class Messenger:
    def __init__(self):
        self.messages: OrderedDict[int, Message] = OrderedDict()
        self._next_id = 0
        self._expiry_heap: List[Tuple[float, int]] = []

    def add_message(self, message: Message) -> int:
        message_id = self._next_id
        self.messages[message_id] = message
        self._next_id += 1

        if message.duration not in (Message.DURATION_PERMANENT,):
            expiry: float = message.created_at + message.duration
            heapq.heappush(self._expiry_heap, (expiry, message_id))
        return message_id

    def remove_message(self, message_id: int) -> None:
        self.messages.pop(message_id, None)

    def clear_messages(self) -> None:
        self.messages.clear()
        self._expiry_heap.clear()

    def get_visible_messages(self, auto_update_before: bool = True) -> list[Message]:
        if auto_update_before:
            self.update(0)

        return [msg for msg in self.messages.values() if msg.visible]

    def update(self, delta_time: float = 0) -> None:
        now = datetime.now().timestamp()
        while self._expiry_heap and self._expiry_heap[0][0] <= now:
            _, msg_id = heapq.heappop(self._expiry_heap)
            msg: Message | None = self.messages.get(msg_id)
            if msg and msg.duration not in (Message.DURATION_PERMANENT,):
                self.remove_message(msg_id)

    def __repr__(self) -> str:
        return f"Messenger(messages={list(self.messages.values())})"

    def __len__(self) -> int:
        return len(self.messages)

    def __getitem__(self, message_id: int) -> Message:
        return self.messages[message_id]

    def __contains__(self, message_id: int) -> bool:
        return message_id in self.messages

    def __iter__(self) -> Iterator[Message]:
        return iter(self.messages.values())

    def __delitem__(self, message_id: int) -> None:
        self.remove_message(message_id)

    def __setitem__(self, message_id: int, message: Message) -> None:
        assert isinstance(message, Message), "Value must be an instance of Message"
        self.messages[message_id] = message

    def dump(self) -> Dict[str, Any]:
        return {
            "messages": {msg_id: msg.dump() for msg_id, msg in self.messages.items()},
            "next_id": self._next_id,
            "expiry_heap": self._expiry_heap,
        }

    def load(self, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        self.__dict__.update(state)
        self.messages = OrderedDict()
        for msg_id, msg_data in copy(state.get("messages", {})).items():
            msg_data = copy(msg_data)
            _cls: Type[Message] = cast(Type[Message], EntityManager.dynamic_import(msg_data.get("cls_ref", "")))
            msg_data.pop("cls_ref", None)
            msg_data.pop("created_at", None)
            self.messages[int(msg_id)] = _cls(**msg_data)

        self._next_id = int(max(self.messages.keys(), default=0)) + 1 if self.messages else 0
        self.messages = OrderedDict(sorted(self.messages.items()))
        self._expiry_heap = [
            (msg.created_at + msg.duration, msg_id)
            for msg_id, msg in self.messages.items()
            if msg.duration not in (Message.DURATION_PERMANENT,)
        ]
        heapq.heapify(self._expiry_heap)
        self.update(0)
