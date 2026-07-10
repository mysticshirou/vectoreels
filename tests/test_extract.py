import io

from yt_dlp.networking.common import Response
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.utils import ExtractorError

from vectoreels.download.extract import _is_auth_failure


def _http_error(content_type: str) -> HTTPError:
    response = Response(
        fp=io.BytesIO(b""),
        url="https://i.instagram.com/api/v1/media/1/info/",
        headers={"Content-Type": content_type},
        status=404,
        reason="Not Found",
    )
    return HTTPError(response)


def test_is_auth_failure_true_for_html_response() -> None:
    error = ExtractorError("boom", cause=_http_error("text/html; charset=utf-8"))
    assert _is_auth_failure(error) is True


def test_is_auth_failure_false_for_json_response() -> None:
    error = ExtractorError("boom", cause=_http_error("application/json"))
    assert _is_auth_failure(error) is False


def test_is_auth_failure_false_without_an_http_cause() -> None:
    error = ExtractorError("boom", cause=ValueError("not an http error"))
    assert _is_auth_failure(error) is False
