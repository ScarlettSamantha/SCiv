from dataclasses import dataclass


DEFAULT_WINDOW_STATE_TOLERANCE_PX = 2


@dataclass(frozen=True, slots=True)
class WindowState:
    origin: tuple[int, int]
    size: tuple[int, int]


def window_state_is_valid(state: WindowState) -> bool:
    return state.size[0] > 0 and state.size[1] > 0


def window_state_differs(
    left: WindowState,
    right: WindowState,
    tolerance_px: int = DEFAULT_WINDOW_STATE_TOLERANCE_PX,
) -> bool:
    threshold = max(0, int(tolerance_px))

    return any(
        abs(lhs - rhs) > threshold
        for lhs, rhs in (
            (left.origin[0], right.origin[0]),
            (left.origin[1], right.origin[1]),
            (left.size[0], right.size[0]),
            (left.size[1], right.size[1]),
        )
    )
