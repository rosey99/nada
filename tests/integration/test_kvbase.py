"""Integration tests for the kvstore class in nada.redis.client.redis_data."""

import pytest


from nada.redis.client.redis_data import KVBase





# ---------------------------------------------------------------------------
# Tests – get_services
# ---------------------------------------------------------------------------

def test_get_services_empty(kvstore):
    """When no services have been registered, get_services returns []."""
    result = kvstore.get_services()
    assert result == []


def test_get_services_returns_registered_services(kvstore):
    """Services added via SADD are reflected in get_services."""
    kvstore.redis.sadd(kvstore.prefix, "svc_a")
    kvstore.redis.sadd(kvstore.prefix, "svc_b")

    result = kvstore.get_services()

    assert sorted(result) == ["svc_a", "svc_b"]


def test_get_services_returns_unique_values(kvstore):
    """Redis sets are unique – duplicates are not returned twice."""
    kvstore.redis.sadd(kvstore.prefix, "svc_a")
    kvstore.redis.sadd(kvstore.prefix, "svc_a")

    result = kvstore.get_services()
    assert len(result) == 1
    assert "svc_a" in result


# ---------------------------------------------------------------------------
# Tests – add_service_keys / get_service_all
# ---------------------------------------------------------------------------

def test_add_service_keys_and_get_all(kvstore):
    """Set a few keys for a service and verify get_service_all returns them."""
    keys = ["k1", "k2", "k3"]
    values = ["v1", "v2", "v3"]
    kvstore.add_service_keys("my_service", keys, values)

    result = kvstore.get_service_all("my_service")

    assert result == {"k1": "v1", "k2": "v2", "k3": "v3"}


def test_add_service_keys_overwrites_existing_value(kvstore):
    """Re-adding the same key updates the value."""
    kvstore.add_service_keys("svc", ["key_a"], ["first"])
    kvstore.add_service_keys("svc", ["key_a"], ["second"])

    result = kvstore.get_service_all("svc")
    assert result == {"key_a": "second"}


def test_add_service_keys_empty_lists(kvstore):
    """Passing empty key/value lists should succeed (no-op)."""
    result = kvstore.add_service_keys("svc", [], [])
    # fcall returns the number of keys set (0 in this case)
    assert result == 0


def test_get_service_all_empty(kvstore):
    """A service with no keys returns an empty dict."""
    result = kvstore.get_service_all("no_keys_svc")
    assert result == {}


def test_add_service_keys_multiple_services_isolated(kvstore):
    """Keys for one service must not leak into another service."""
    kvstore.add_service_keys("svc_x", ["shared_key"], ["value_x"])
    kvstore.add_service_keys("svc_y", ["shared_key"], ["value_y"])

    x_data = kvstore.get_service_all("svc_x")
    y_data = kvstore.get_service_all("svc_y")

    assert x_data == {"shared_key": "value_x"}
    assert y_data == {"shared_key": "value_y"}


# ---------------------------------------------------------------------------
# Tests – add_service_keys validation
# ---------------------------------------------------------------------------

def test_add_service_keys_mismatched_lengths_raises(kvstore):
    """If keys and values lists differ in length, a ValueError is raised."""
    with pytest.raises(ValueError, match="number of keys and values must be equal"):
        kvstore.add_service_keys("svc", ["k1", "k2"], ["v1"])


def test_add_service_keys_mismatched_lengths_different(kvstore):
    """Error message should report the actual counts."""
    with pytest.raises(ValueError, match="got 3 keys and 1 values"):
        kvstore.add_service_keys("svc", ["a", "b", "c"], ["v1"])


# ---------------------------------------------------------------------------
# Tests – delete_service_keys
# ---------------------------------------------------------------------------

def test_delete_service_keys_removes_specific_keys(kvstore):
    """Deleting specific keys removes only those keys."""
    kvstore.add_service_keys("svc", ["k1", "k2", "k3"], ["v1", "v2", "v3"])
    kvstore.delete_service_keys("svc", ["k2"])

    result = kvstore.get_service_all("svc")
    assert result == {"k1": "v1", "k3": "v3"}


def test_delete_service_keys_nonexistent_is_noop(kvstore):
    """Deleting a key that doesn't exist should not raise."""
    kvstore.add_service_keys("svc", ["k1"], ["v1"])
    # Should not raise
    kvstore.delete_service_keys("svc", ["ghost_key"])
    assert kvstore.get_service_all("svc") == {"k1": "v1"}


def test_delete_service_keys_empty_list(kvstore):
    """Deleting with an empty list is a no-op."""
    kvstore.add_service_keys("svc", ["k1"], ["v1"])
    kvstore.delete_service_keys("svc", [])
    assert kvstore.get_service_all("svc") == {"k1": "v1"}


# ---------------------------------------------------------------------------
# Tests – delete_service
# ---------------------------------------------------------------------------

def test_delete_service_removes_all_keys_and_set(kvstore):
    """delete_service should remove all keys for a service and the set entry."""
    kvstore.add_service_keys("svc", ["k1", "k2"], ["v1", "v2"])

    kvstore.delete_service("svc")

    assert "svc" not in kvstore.get_services()
    assert kvstore.get_service_all("svc") == {}


def test_delete_service_nonexistent_is_noop(kvstore):
    """Deleting a service that doesn't exist should not raise."""
    # Should not raise
    kvstore.delete_service("ghost_service")
    assert kvstore.get_services() == []


# ---------------------------------------------------------------------------
# Tests – prefix isolation
# ---------------------------------------------------------------------------

def test_different_prefixes_are_isolated(redis_client):
    """Two kvstore instances with different prefixes must not see each
    other's data."""
    svc_a = KVBase(redis_con=redis_client, service_prefix="prefix_alpha")
    svc_b = KVBase(redis_con=redis_client, service_prefix="prefix_beta")

    svc_a.add_service_keys("a_svc", ["k1"], ["val1"])
    svc_b.add_service_keys("a_svc", ["k1"], ["val2"])

    assert svc_a.get_service_all("a_svc") == {"k1": "val1"}
    assert svc_b.get_service_all("a_svc") == {"k1": "val2"}

    # Services are stored under their respective prefixes
    assert "a_svc" in svc_a.get_services()
    assert "a_svc" in svc_b.get_services()
