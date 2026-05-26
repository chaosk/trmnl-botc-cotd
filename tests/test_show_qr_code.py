"""Wiki QR toggle from plugin settings."""

import importlib.util
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"


def _transform():
    spec = importlib.util.spec_from_file_location("transform", SRC / "transform.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["transform"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_show_qr_code_default_true() -> None:
    mod = _transform()
    assert mod.show_qr_code_from_input({}) is True


def test_show_qr_code_false_strings() -> None:
    mod = _transform()
    for val in (False, "false", "no", "0", "off"):
        assert mod.show_qr_code_from_input({"show_qr_code": val}) is False


def test_show_qr_code_true_values() -> None:
    mod = _transform()
    for val in (True, "true", "yes", "1"):
        assert mod.show_qr_code_from_input({"show_qr_code": val}) is True


def test_show_qr_code_from_custom_fields() -> None:
    mod = _transform()
    assert (
        mod.show_qr_code_from_input(
            {"trmnl": {"plugin_settings": {"custom_fields_values": {"show_qr_code": False}}}}
        )
        is False
    )
