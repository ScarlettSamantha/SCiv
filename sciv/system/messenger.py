import heapq
from datetime import datetime
from typing import Any, Callable, Dict, Iterator, List, OrderedDict, Tuple

from kivy.uix.image import Image
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class Message:
    DURATION_DEFAULT: float = 5.0  # Default duration for messages
    DURATION_PERMANENT: float = -1.0  # Permanent messages do not disappear

    on_click: Callable[..., Any] | None = None

    def __init__(
        self,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStrOrNone = None,
        duration: float = DURATION_DEFAULT,
        color: tuple[float, ...] = (1.0, 1.0, 1.0, 1.0),
        icon: str | Image = "",
        visible: bool = True,
        is_closable: bool = True,
        is_clickable: bool = False,
        is_blocking: bool = False,
        is_disabled: bool = False,
        on_click_arguments: Dict[Any, Any] = {},
    ):
        self.text: T_TranslationOrStr = text
        self.tooltip: T_TranslationOrStrOrNone = tooltip
        self.duration: float = duration
        self.color: Tuple[float, ...] = color

        if icon == "":
            self.icon: Image | None = None
        elif isinstance(icon, str):
            self.icon: Image | None = Image(source=icon)
        else:
            self.icon: Image | None = icon

        self.visible: bool = visible
        self.created_at: float = datetime.now().timestamp()
        self.is_closable: bool = is_closable
        self.is_blocking: bool = is_blocking
        self.is_clickable: bool = is_clickable
        self.is_disabled: bool = is_disabled
        self.on_click_arguments: Dict[Any, Any] = on_click_arguments

    def hide(self) -> None:
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def toggle_visibility(self) -> None:
        self.visible = not self.visible

    def execute_click(self, *args: List[Any], **kwargs: Dict[str, Any]) -> Any:
        if self.on_click and not self.is_disabled:
            return self.on_click(*args, **kwargs, **self.on_click_arguments)
        return None

    def __repr__(self) -> str:
        return f"Message(text={self.text}, duration={self.duration}, color={self.color}, icon={self.icon})"

    def dump(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "tooltip": self.tooltip,
            "duration": self.duration,
            "color": self.color,
            "icon": self.icon,
            "visible": self.visible,
            "created_at": self.created_at,
            "is_closable": self.is_closable,
            "is_blocking": self.is_blocking,
            "is_clickable": self.is_clickable,
            "is_disabled": self.is_disabled,
            "on_click_arguments": self.on_click_arguments,
        }

    def load(self, state: Dict[str, Any]) -> None:
        self.text = state.get("text", "")
        self.tooltip = state.get("tooltip", None)
        self.duration = state.get("duration", self.DURATION_DEFAULT)
        self.color = tuple(state.get("color", (1.0, 1.0, 1.0, 1.0)))
        self.icon = state.get("icon", "") if isinstance(state.get("icon"), str) else Image(source=state.get("icon", ""))
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
            text=data.get("text", ""),
            tooltip=data.get("tooltip"),
            duration=data.get("duration", cls.DURATION_DEFAULT),
            color=tuple(data.get("color", (1.0, 1.0, 1.0, 1.0))),  # type: ignore
            icon=data.get("icon", ""),
            visible=data.get("visible", True),
            is_closable=data.get("is_closable", True),
            is_blocking=data.get("is_blocking", False),
            is_clickable=data.get("is_clickable", False),
            is_disabled=data.get("is_disabled", False),
        )
        message.on_click = data.get("on_click", None)
        if isinstance(message.on_click, str):
            from managers.entity import EntityManager

            message.on_click = EntityManager.dynamic_import(message.on_click)  # type: ignore

        message.created_at = data.get("created_at", datetime.now().timestamp())
        return message

    @classmethod
    def permanent(
        cls,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStr | None = None,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        icon: str = "",
        is_closable: bool = True,
        is_blocking: bool = False,
    ) -> "Message":
        return cls(
            text=text,
            tooltip=tooltip,
            duration=cls.DURATION_PERMANENT,
            color=color,
            icon=icon,
            visible=True,
            is_closable=is_closable,
            is_blocking=is_blocking,
        )

    @classmethod
    def temporary(
        cls,
        text: T_TranslationOrStr,
        tooltip: T_TranslationOrStr | None = None,
        duration: float = DURATION_DEFAULT,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        icon: str = "",
        is_closable: bool = True,
        is_blocking: bool = False,
    ) -> "Message":
        return cls(
            text=text,
            tooltip=tooltip,
            duration=duration,
            color=color,
            icon=icon,
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
            expiry = message.created_at + message.duration
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
        state: Dict[str, Any] = self.__dict__
        state["messages"] = {msg_id: msg.__dict__ for msg_id, msg in self.messages.items()}
        return state

    def load(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.messages = OrderedDict(
            (msg_id, Message(**msg_data)) for msg_id, msg_data in state.get("messages", {}).items()
        )
        self._next_id = max(self.messages.keys(), default=0) + 1 if self.messages else 0
        self.messages = OrderedDict(sorted(self.messages.items()))
