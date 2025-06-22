import functools
from typing import Any, Callable, Dict, Tuple
from direct.stdpy import threading


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
    delay: float = 1.0, *, execute_last_event_on_end: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        lock = threading.Lock()
        blocked = False
        last_args: Tuple[Any, ...] = ()
        last_kwargs: Dict[str, Any] = {}

        def _release():
            nonlocal blocked, last_args, last_kwargs
            with lock:
                blocked = False
                if execute_last_event_on_end and last_args or last_kwargs:
                    fn(*last_args, **last_kwargs)
                    last_args, last_kwargs = (), {}
                    blocked = True
                    t = threading.Timer(delay, _release)
                    t.daemon = True
                    t.start()

        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> None:
            nonlocal blocked, last_args, last_kwargs
            with lock:
                if not blocked:
                    fn(*args, **kwargs)
                    blocked = True
                    t = threading.Timer(delay, _release)
                    t.daemon = True
                    t.start()
                else:
                    if execute_last_event_on_end:
                        last_args = args
                        last_kwargs = kwargs

        return wrapped

    return decorator
