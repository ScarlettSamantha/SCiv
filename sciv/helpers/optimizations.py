import functools
from typing import Any, Callable, Dict, Tuple

from direct.stdpy import threading
from kivy.clock import Clock


def debounce(delay: float = 1.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        pending: threading.Timer | None = None
        lock = threading.Lock()

        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> None:
            nonlocal pending

            def run_it():
                fn(*args, **kwargs)

            with lock:
                if pending is not None:
                    pending.cancel()
                pending = threading.Timer(delay, run_it)
                pending.daemon = True
                pending.start()

        return wrapped

    return decorator


def throttle(
    delay: float = 1.0,
    execute_last_event_on_end: bool = False,
    run_on_main_thread: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        lock = threading.Lock()
        blocked = False
        last_args: Tuple[Any, ...] = ()
        last_kwargs: Dict[str, Any] = {}

        def _schedule_call(a: Tuple[Any, ...], k: Dict[str, Any]) -> None:
            if run_on_main_thread:

                def _cb(_: float) -> None:
                    fn(*a, **k)

                Clock.schedule_once(_cb, 0)  # type: ignore
            else:
                fn(*a, **k)

        def _release() -> None:
            nonlocal blocked, last_args, last_kwargs
            with lock:
                blocked = False
                if execute_last_event_on_end and (last_args or last_kwargs):
                    _schedule_call(last_args, last_kwargs)
                    last_args, last_kwargs = (), {}
                    blocked = True
                    _schedule_release()

        def _schedule_release() -> None:
            if run_on_main_thread:
                Clock.schedule_once(lambda _: _release(), delay)  # type: ignore
            else:
                t = threading.Timer(delay, _release)
                t.daemon = True
                t.start()

        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> None:
            nonlocal blocked, last_args, last_kwargs
            with lock:
                if not blocked:
                    _schedule_call(args, kwargs)
                    blocked = True
                    _schedule_release()
                else:
                    if execute_last_event_on_end:
                        last_args = args
                        last_kwargs = kwargs

        return wrapped

    return decorator
