"""Integration tests for the kvstore class in nada.redis.client.redis_data."""

import pytest


from nada.redis.client.redis_data import KVBase





# ---------------------------------------------------------------------------
# Tests – get_services
# ---------------------------------------------------------------------------

async def test_get_services_empty(kvstore):
    """When no services have been registered, get_services returns []."""
    result = await kvstore.get_services()
    assert result == []


async def test_get_services_returns_registered_services(kvstore):
    """Services added via SADD are reflected in get_services."""
    await kvstore.redis.sadd(kvstore.prefix, "svc_a")
    await kvstore.redis.sadd(kvstore.prefix, "svc_b")

    result = await kvstore.get_services()

    assert sorted(result) == ["svc_a", "svc_b"]


async def test_get_services_returns_unique_values(kvstore):
    """Redis sets are unique – duplicates are not returned twice."""
    await kvstore.redis.sadd(kvstore.prefix, "svc_a")
    await kvstore.redis.sadd(kvstore.prefix, "svc_a")

    result = await kvstore.get_services()
    assert len(result) == 1
    assert "svc_a" in result


# ---------------------------------------------------------------------------
# Tests – add_service_keys / get_service_all
# ---------------------------------------------------------------------------

async def test_add_service_keys_and_get_all(kvstore):
    """Set a few keys for a service and verify get_service_all returns them."""
    keys = ["k1", "k2", "k3"]
    values = ["v1", "v2", "v3"]
    await kvstore.add_service_keys("my_service", keys, values)

    result = await kvstore.get_service_all("my_service")

    assert result == {"k1": "v1", "k2": "v2", "k3": "v3"}


async def test_add_service_keys_overwrites_existing_value(kvstore):
    """Re-adding the same key updates the value."""
    await kvstore.add_service_keys("svc", ["key_a"], ["first"])
    await kvstore.add_service_keys("svc", ["key_a"], ["second"])

    result = await kvstore.get_service_all("svc")
    assert result == {"key_a": "second"}


async def test_add_service_keys_empty_lists(kvstore):
    """Passing empty key/value lists should succeed (no-op)."""
    result = await kvstore.add_service_keys("svc", [], [])
    # fcall returns the number of keys set (0 in this case)
    assert result == 0


async def test_get_service_all_empty(kvstore):
    """A service with no keys returns an empty dict."""
    result = await kvstore.get_service_all("no_keys_svc")
    assert result == {}


async def test_add_service_keys_multiple_services_isolated(kvstore):
    """Keys for one service must not leak into another service."""
    await kvstore.add_service_keys("svc_x", ["shared_key"], ["value_x"])
    await kvstore.add_service_keys("svc_y", ["shared_key"], ["value_y"])

    x_data = await kvstore.get_service_all("svc_x")
    y_data = await kvstore.get_service_all("svc_y")

    assert x_data == {"shared_key": "value_x"}
    assert y_data == {"shared_key": "value_y"}


# ---------------------------------------------------------------------------
# Tests – add_service_keys validation
# ---------------------------------------------------------------------------

async def test_add_service_keys_mismatched_lengths_raises(kvstore):
    """If keys and values lists differ in length, a ValueError is raised."""
    with pytest.raises(ValueError, match="number of keys and values must be equal"):
        await kvstore.add_service_keys("svc", ["k1", "k2"], ["v1"])


async def test_add_service_keys_mismatched_lengths_different(kvstore):
    """Error message should report the actual counts."""
    with pytest.raises(ValueError, match="got 3 keys and 1 values"):
        await kvstore.add_service_keys("svc", ["a", "b", "c"], ["v1"])


# ---------------------------------------------------------------------------
# Tests – delete_service_keys
# ---------------------------------------------------------------------------

async def test_delete_service_keys_removes_specific_keys(kvstore):
    """Deleting specific keys removes only those keys."""
    await kvstore.add_service_keys("svc", ["k1", "k2", "k3"], ["v1", "v2", "v3"])
    await kvstore.delete_service_keys("svc", ["k2"])

    result = await kvstore.get_service_all("svc")
    assert result == {"k1": "v1", "k3": "v3"}


async def test_delete_service_keys_nonexistent_is_noop(kvstore):
    """Deleting a key that doesn't exist should not raise."""
    await kvstore.add_service_keys("svc", ["k1"], ["v1"])
    # Should not raise
    await kvstore.delete_service_keys("svc", ["ghost_key"])
    assert await kvstore.get_service_all("svc") == {"k1": "v1"}


async def test_delete_service_keys_empty_list(kvstore):
    """Deleting with an empty list is a no-op."""
    await kvstore.add_service_keys("svc", ["k1"], ["v1"])
    await kvstore.delete_service_keys("svc", [])
    assert await kvstore.get_service_all("svc") == {"k1": "v1"}


# ---------------------------------------------------------------------------
# Tests – delete_service
# ---------------------------------------------------------------------------

async def test_delete_service_removes_all_keys_and_set(kvstore):
    """delete_service should remove all keys for a service and the set entry."""
    await kvstore.add_service_keys("svc", ["k1", "k2"], ["v1", "v2"])

    await kvstore.delete_service("svc")

    assert "svc" not in await kvstore.get_services()
    assert await kvstore.get_service_all("svc") == {}


async def test_delete_service_nonexistent_is_noop(kvstore):
    """Deleting a service that doesn't exist should not raise."""
    # Should not raise
    await kvstore.delete_service("ghost_service")
    assert await kvstore.get_services() == []


# ---------------------------------------------------------------------------
# Tests – prefix isolation
# ---------------------------------------------------------------------------

async def test_different_prefixes_are_isolated(redis_client):
    """Two kvstore instances with different prefixes must not see each
    other's data."""
    svc_a = KVBase(redis_con=redis_client, service_prefix="prefix_alpha")
    svc_b = KVBase(redis_con=redis_client, service_prefix="prefix_beta")

    await svc_a.add_service_keys("a_svc", ["k1"], ["val1"])
    await svc_b.add_service_keys("a_svc", ["k1"], ["val2"])

    assert await svc_a.get_service_all("a_svc") == {"k1": "val1"}
    assert await svc_b.get_service_all("a_svc") == {"k1": "val2"}

    # Services are stored under their respective prefixes
    assert "a_svc" in await svc_a.get_services()
    assert "a_svc" in await svc_b.get_services()
