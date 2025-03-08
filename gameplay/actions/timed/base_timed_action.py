from threading import Timer
from typing import Callable, Dict, List, Optional, Self

from direct.interval.IntervalGlobal import Func, Sequence, Wait

from system.actions import Action

"""
Base class for timed actions.

This version uses Python’s threading.Timer to schedule a callback after a delay.
It won’t block the main thread in the meantime.
"""


class BaseTimedAction(Action):
    def __init__(
        self,
        delay: int = 1,
        on_callback: Optional[Callable[[Self, Callable, List, Dict], None]] = None,
        on_invoke: Optional[Callable[[Self, List, Dict], None]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.on_the_spot_action = True
        self.targeting_tile_action = False

        self._on_callback: Optional[Callable[[Self, Callable, List, Dict], None]] = on_callback
        self._on_invoke: Optional[Callable[[Self, List, Dict], None]] = on_invoke
        self._delay: int = delay
        self._timer: Optional[Timer] = None  # Holds reference to avoid GC.
        self._logger = self.logger.getChild("timed")
        self.logger = self.logger.getChild("timed").getChild(str(self.name))

    def _timed_callback(self, *args, **kwargs) -> None:
        """Invoked by the timer after the delay."""
        self._logger.info(f"Action {self.name} has been completed and the callback has been invoked.")
        if self._on_callback is not None:
            # Pass our parent's run() so that the callback can chain it when ready.
            self._on_callback(self, super().run, *args, **kwargs)
        else:
            super().run()

    def _run_invoke(self, *args, **kwargs) -> None:
        """Called right before setting up the timer (useful for immediate side effects)."""
        if self._on_invoke is not None:
            self._logger.info(f"Invoking action {self.name}.")
            self._on_invoke(self, *args, **kwargs)

    def run(self) -> None:
        """Starts the timed action in a non-blocking fashion."""
        self._run_invoke()
        self._logger.info(f"Starting timer for action {self.name} with a delay of {self._delay} seconds.")
        sequence: Sequence = Sequence(Wait(self._delay), Func(self._timed_callback))
        sequence.start()
