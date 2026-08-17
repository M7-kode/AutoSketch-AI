import cv2
import numpy as np
import pytest

from vision import image_loader
from vision.image_loader import get_image_info, load_image, load_image_from_url


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"{self.status_code} Client Error")


def png_bytes(image):
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return buffer.tobytes()


@pytest.fixture
def sample_image():
    image = np.zeros((8, 12, 3), dtype=np.uint8)
    image[:, :6] = (0, 0, 255)
    return image


def test_info_reports_the_dimensions(sample_image):
    assert get_image_info(sample_image) == {"width": 12, "height": 8, "channels": 3}


def test_a_missing_file_is_reported_clearly(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_image(str(tmp_path / "nope.png"))


def test_an_image_file_is_loaded(tmp_path, sample_image):
    path = tmp_path / "image.png"
    cv2.imwrite(str(path), sample_image)

    assert load_image(str(path)).shape == sample_image.shape


def test_an_image_url_is_decoded(monkeypatch, sample_image):
    monkeypatch.setattr(image_loader.requests, "get",
                        lambda url, timeout=None: FakeResponse(png_bytes(sample_image)))

    loaded = load_image_from_url("https://example.com/image.png")

    assert loaded.shape == sample_image.shape


def test_a_page_that_is_not_an_image_is_rejected(monkeypatch):
    monkeypatch.setattr(image_loader.requests, "get",
                        lambda url, timeout=None: FakeResponse(b"<html>pas une image</html>"))

    with pytest.raises(ValueError):
        load_image_from_url("https://example.com/page")


def test_a_broken_link_is_reported(monkeypatch):
    monkeypatch.setattr(image_loader.requests, "get",
                        lambda url, timeout=None: FakeResponse(b"", status_code=404))

    with pytest.raises(RuntimeError):
        load_image_from_url("https://example.com/missing.png")


def test_the_download_cannot_hang_forever(monkeypatch, sample_image):
    # Sans delai maximum, une URL lente figerait l'application.
    seen = {}

    def fake_get(url, timeout=None):
        seen["timeout"] = timeout
        return FakeResponse(png_bytes(sample_image))

    monkeypatch.setattr(image_loader.requests, "get", fake_get)
    load_image_from_url("https://example.com/image.png")

    assert seen["timeout"] is not None
