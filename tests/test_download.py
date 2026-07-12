"""
Integration test: verify that Vosk download URLs resolve and serve ZIP files.
Uses HEAD requests only — does not download full models.
Marked as 'network' so you can skip in offline CI with: pytest -m "not network"
"""

import pytest
from urllib.request import urlopen, Request
from vosk_catalog import VOSK_MODELS


def _one_model_per_language():
    """Pick the first model for each language to minimize requests."""
    seen = set()
    result = []
    for m in VOSK_MODELS:
        if m["lang"] not in seen:
            seen.add(m["lang"])
            result.append(m)
    return result


@pytest.mark.network
class TestVoskUrls:
    @pytest.mark.parametrize("model", _one_model_per_language(),
                             ids=lambda m: m["name"])
    def test_url_resolves(self, model):
        """Confirm the download URL returns 200 with a ZIP content-type."""
        req = Request(model["url"], method="HEAD",
                      headers={"User-Agent": "PolyScribe-test/1.0"})
        try:
            resp = urlopen(req, timeout=15)
            assert resp.status == 200, f"Got {resp.status} for {model['name']}"
            content_type = resp.headers.get("Content-Type", "")
            assert "zip" in content_type or "octet" in content_type, (
                f"Unexpected content-type '{content_type}' for {model['name']}")
        except Exception as e:
            pytest.fail(f"URL failed for {model['name']}: {e}")
