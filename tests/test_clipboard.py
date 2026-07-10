from __future__ import annotations

from typing import Any

from localvoice.clipboard import copy_text


def test_wl_copy_receives_text_only_via_stdin() -> None:
    captured: dict[str, Any] = {}

    def runner(args: list[str], **kwargs: Any) -> None:
        captured["args"], captured["kwargs"] = args, kwargs

    payload_text = "hello; $(never-a-shell)"
    copy_text(payload_text, runner=runner)  # type: ignore[arg-type]
    assert payload_text not in captured["args"]
    assert captured["args"] == ["wl-copy", "--type", "text/plain;charset=utf-8"]
    assert captured["kwargs"]["input"] == payload_text.encode()
    assert captured["kwargs"]["shell"] is False
