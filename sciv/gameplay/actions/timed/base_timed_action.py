from typing import Any, Callable, Dict, List, Optional, Self

from direct.interval.IntervalGlobal import Func, Sequence, Wait

from system.actions import Action


class BaseTimedAction(Action):
    def __init__(
        self,
        delay: int = 1,
        on_callback: Optional[Callable[[Self, Callable[..., None], List[Any], Dict[str, Any]], None]] = None,
        on_invoke: Optional[Callable[[Self, List[Any], Dict[str, Any]], None]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self.on_the_spot_action = True
        self.targeting_tile_action = False

        self._on_callback: Optional[Callable[[Self, Callable[..., None], List[Any], Dict[str, Any]], None]] = (
            on_callback
        )
        self._on_invoke: Optional[Callable[[Self, List[Any], Dict[str, Any]], None]] = on_invoke
        self._delay: int = delay
        self.sequence: Optional[Sequence] = None  # Holds reference to avoid GC.
        self._logger = self.logger.getChild("timed")
        self.logger = self.logger.getChild("timed").getChild(str(self.name))

    def _timed_callback(self, *args: Any, **kwargs: Any) -> None:
        self._logger.info(f"Action {self.name} has been completed and the callback has been invoked.")
        if self._on_callback is not None:
            self._on_callback(self, super().run, *args, **kwargs)
        else:
            super().run()

    def _run_invoke(self, *args: Any, **kwargs: Any) -> None:
        if self._on_invoke is not None:
            self._logger.info(f"Invoking action {self.name}.")
            self._on_invoke(self, *args, **kwargs)

    def run(self) -> None:
        self._run_invoke()
        self._logger.info(f"Starting timer for action {self.name} with a delay of {self._delay} seconds.")
        self.sequence = Sequence(Wait(self._delay), Func(self._timed_callback))  # type: ignore
        self.sequence.start()
