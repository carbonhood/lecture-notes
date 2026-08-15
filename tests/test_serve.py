"""Tests for mobile upload server helpers."""

from lecture_notes.serve import _guess_local_ip, _parse_multipart


def test_guess_local_ip_returns_string() -> None:
    ip = _guess_local_ip()
    assert isinstance(ip, str)
    assert ip


def test_parse_multipart_text_and_file() -> None:
    boundary = "----Bound123"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="lecture_name"\r\n\r\n'
        "Week 1\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="audio"; filename="a.wav"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
        "RIFFDATA\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    form = _parse_multipart(f"multipart/form-data; boundary={boundary}", body)
    assert form.values["lecture_name"] == "Week 1"
    assert form.files["audio"].filename == "a.wav"
    assert form.files["audio"].data == b"RIFFDATA"
