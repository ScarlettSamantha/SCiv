from pathlib import Path
import importlib
import sys


ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = ROOT / "sciv"
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

window_state = importlib.import_module("helpers.window_state")

WindowState = window_state.WindowState
window_state_differs = window_state.window_state_differs
window_state_is_valid = window_state.window_state_is_valid


def test_window_state_is_valid_requires_positive_size() -> None:
    assert window_state_is_valid(WindowState(origin=(100, 200), size=(1920, 1080)))
    assert not window_state_is_valid(WindowState(origin=(100, 200), size=(0, 1080)))
    assert not window_state_is_valid(WindowState(origin=(100, 200), size=(1920, -1)))


def test_window_state_differs_ignores_small_noise_within_tolerance() -> None:
    left = WindowState(origin=(100, 200), size=(1920, 1080))
    right = WindowState(origin=(102, 198), size=(1918, 1082))

    assert not window_state_differs(left, right)


def test_window_state_differs_detects_real_origin_changes() -> None:
    left = WindowState(origin=(100, 200), size=(1920, 1080))
    right = WindowState(origin=(106, 200), size=(1920, 1080))

    assert window_state_differs(left, right)


def test_window_state_differs_detects_real_size_changes() -> None:
    left = WindowState(origin=(100, 200), size=(1920, 1080))
    right = WindowState(origin=(100, 200), size=(1920, 1076))

    assert window_state_differs(left, right)
