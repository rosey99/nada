

from nada.settings import load_providers

def test_load_providers():
    r = load_providers()
    assert r
