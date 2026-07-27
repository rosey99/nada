"""Integration tests for the KVBase class in nada.redis.client.redis_data."""

import pytest
import redis

from nada.redis.client.redis_data import KVBase


# ---------------------------------------------------------------------------
# Lua function definitions used by KVBase via redis.FCALL
# ---------------------------------------------------------------------------
#
# Redis Functions (introduced in Redis 7.0) require a shebang line
# ``#!lua name=<library>`` and functions must be registered with
# ``redis.register_function``.  See:
#   https://redis.io/docs/latest/commands/function-load/
#
# KVBase calls fcall like:
#   fcall('set_keys', key_count, *real_keys, *values)
# Which maps to FCALL set_keys N KEY1 KEY2 ... ARG1 ARG2 ...
# where N = key_count, the first N args after numkeys become KEYS,
# the remainder become ARGS.  So in the Lua function:
#   keys  = real_keys   (the fully-qualified Redis keys to set/delete)
#   args  = values      (the values to set, when applicable)
#
# NOTE: Both functions must be in the same library because loading a
# library with the same name replaces the previous one – if we loaded
# them separately only the last function would survive.

KVBASE_LIBRARY = """\
#!lua name=kvbase_lib
redis.register_function('set_keys', function(keys, args)
    local n = #keys
    for i = 1, n do
        redis.call('SET', keys[i], args[i])
        -- Also add the key to the service set so get_service_all can find it.
        -- The service set name is derived from the key itself:
        -- key = <prefix>:<service>:<name>  =>  set = <prefix>:<service>
        local set_name = keys[i]:match('^(.+:[^:]+):')
        if set_name then
            redis.call('SADD', set_name, keys[i])
            -- Also register the service in the top-level services set.
            -- The prefix is the first two colon-separated parts:
            -- key = <prefix>:<service>:<name>  =>  prefix set = <prefix>
            local prefix = keys[i]:match('^([^:]+:[^:]+):')
            if prefix then
                redis.call('SADD', prefix, keys[i]:match('^([^:]+:[^:]+):[^:]+'))
            end
        end
    end
    return n
end)
redis.register_function('remove_keys', function(keys, args)
    local n = #keys
    for i = 1, n do
        -- Remove from the service set as well
        local set_name = keys[i]:match('^(.+:[^:]+):')
        if set_name then
            redis.call('SREM', set_name, keys[i])
        end
        redis.call('DEL', keys[i])
    end
    return n
end)
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _register_lua_functions(redis_client: redis.Redis):
    """Ensure the Lua functions expected by KVBase are loaded into Redis.

    KVBase uses ``redis.fcall`` to invoke registered functions named
    ``set_keys`` and ``remove_keys``.  In Redis 7+ these must be loaded
    via ``FUNCTION LOAD`` before they can be called.
    """
    # Load (or reload) the library.  FUNCTION LOAD is idempotent –
    # reloading the same code replaces the existing library.
    redis_client.function_load(KVBASE_LIBRARY, replace=True)
    yield
    # Teardown: flush the test database so state doesn't leak between tests.
    redis_client.flushdb()


@pytest.fixture
def kvbase(redis_client: redis.Redis):
    """A KVBase instance backed by the test Redis client."""
    return KVBase(redis_con=redis_client, service_name="test_svc")


# ---------------------------------------------------------------------------
# Tests – get_services
# ---------------------------------------------------------------------------

def test_get_services_empty(kvbase: KVBase):
    """When no services have been registered, get_services returns []."""
    result = kvbase.get_services()
    assert result == []


def test_get_services_returns_registered_services(kvbase: KVBase):
    """Services added via SADD are reflected in get_services."""
    kvbase.redis.sadd(kvbase.prefix, "svc_a")
    kvbase.redis.sadd(kvbase.prefix, "svc_b")

    result = kvbase.get_services()

    assert sorted(result) == ["svc_a", "svc_b"]


def test_get_services_returns_unique_values(kvbase: KVBase):
    """Redis sets are unique – duplicates are not returned twice."""
    kvbase.redis.sadd(kvbase.prefix, "svc_a")
    kvbase.redis.sadd(kvbase.prefix, "svc_a")

    result = kvbase.get_services()
    assert len(result) == 1
    assert "svc_a" in result


# ---------------------------------------------------------------------------
# Tests – add_service_keys / get_service_all
# ---------------------------------------------------------------------------

def test_add_service_keys_and_get_all(kvbase: KVBase):
    """Set a few keys for a service and verify get_service_all returns them."""
    keys = ["k1", "k2", "k3"]
    values = ["v1", "v2", "v3"]
    kvbase.add_service_keys("my_service", keys, values)

    result = kvbase.get_service_all("my_service")

    assert result == {"k1": "v1", "k2": "v2", "k3": "v3"}


def test_add_service_keys_overwrites_existing_value(kvbase: KVBase):
    """Re-adding the same key updates the value."""
    kvbase.add_service_keys("svc", ["key_a"], ["first"])
    kvbase.add_service_keys("svc", ["key_a"], ["second"])

    result = kvbase.get_service_all("svc")
    assert result == {"key_a": "second"}


def test_add_service_keys_empty_lists(kvbase: KVBase):
    """Passing empty key/value lists should succeed (no-op)."""
    result = kvbase.add_service_keys("svc", [], [])
    # fcall returns the number of keys set (0 in this case)
    assert result == 0


def test_get_service_all_empty(kvbase: KVBase):
    """A service with no keys returns an empty dict."""
    result = kvbase.get_service_all("no_keys_svc")
    assert result == {}


def test_add_service_keys_multiple_services_isolated(kvbase: KVBase):
    """Keys for one service must not leak into another service."""
    kvbase.add_service_keys("svc_x", ["shared_key"], ["value_x"])
    kvbase.add_service_keys("svc_y", ["shared_key"], ["value_y"])

    x_data = kvbase.get_service_all("svc_x")
    y_data = kvbase.get_service_all("svc_y")

    assert x_data == {"shared_key": "value_x"}
    assert y_data == {"shared_key": "value_y"}


# ---------------------------------------------------------------------------
# Tests – add_service_keys validation
# ---------------------------------------------------------------------------

def test_add_service_keys_mismatched_lengths_raises(kvbase: KVBase):
    """If keys and values lists differ in length, a ValueError is raised."""
    with pytest.raises(ValueError, match="number of keys and values must be equal"):
        kvbase.add_service_keys("svc", ["k1", "k2"], ["v1"])


def test_add_service_keys_mismatched_lengths_different(kvbase: KVBase):
    """Error message should report the actual counts."""
    with pytest.raises(ValueError, match="got 3 keys and 1 values"):
        kvbase.add_service_keys("svc", ["a", "b", "c"], ["v1"])


# ---------------------------------------------------------------------------
# Tests – delete_service_keys
# ---------------------------------------------------------------------------

def test_delete_service_keys_removes_specific_keys(kvbase: KVBase):
    """Deleting specific keys removes only those keys."""
    kvbase.add_service_keys("svc", ["k1", "k2", "k3"], ["v1", "v2", "v3"])
    kvbase.delete_service_keys("svc", ["k2"])

    result = kvbase.get_service_all("svc")
    assert result == {"k1": "v1", "k3": "v3"}


def test_delete_service_keys_nonexistent_is_noop(kvbase: KVBase):
    """Deleting a key that doesn't exist should not raise."""
    kvbase.add_service_keys("svc", ["k1"], ["v1"])
    # Should not raise
    kvbase.delete_service_keys("svc", ["ghost_key"])
    assert kvbase.get_service_all("svc") == {"k1": "v1"}


def test_delete_service_keys_empty_list(kvbase: KVBase):
    """Deleting with an empty list is a no-op."""
    kvbase.add_service_keys("svc", ["k1"], ["v1"])
    kvbase.delete_service_keys("svc", [])
    assert kvbase.get_service_all("svc") == {"k1": "v1"}


def test_delete_all_keys_leaves_service_set(kvbase: KVBase):
    """After removing all data keys the service set entry should still
    exist (only delete_service removes the set entry)."""
    kvbase.redis.sadd(kvbase.prefix, "svc")
    kvbase.add_service_keys("svc", ["k1"], ["v1"])
    kvbase.delete_service_keys("svc", ["k1"])

    # The service should still be listed
    assert "svc" in kvbase.get_services()
    # But its data should be empty
    assert kvbase.get_service_all("svc") == {}


# ---------------------------------------------------------------------------
# Tests – delete_service
# ---------------------------------------------------------------------------

def test_delete_service_removes_all_keys_and_set(kvbase: KVBase):
    """delete_service should remove all keys for a service and the set entry."""
    kvbase.redis.sadd(kvbase.prefix, "svc")
    kvbase.add_service_keys("svc", ["k1", "k2"], ["v1", "v2"])

    kvbase.delete_service("svc")

    assert "svc" not in kvbase.get_services()
    assert kvbase.get_service_all("svc") == {}


def test_delete_service_nonexistent_is_noop(kvbase: KVBase):
    """Deleting a service that doesn't exist should not raise."""
    # Should not raise
    kvbase.delete_service("ghost_service")
    assert kvbase.get_services() == []


# ---------------------------------------------------------------------------
# Tests – prefix isolation
# ---------------------------------------------------------------------------

def test_different_prefixes_are_isolated(redis_client: redis.Redis):
    """Two KVBase instances with different prefixes must not see each
    other's data."""
    svc_a = KVBase(redis_con=redis_client, service_name="prefix_alpha")
    svc_b = KVBase(redis_con=redis_client, service_name="prefix_beta")

    svc_a.add_service_keys("svc", ["k1"], ["val1"])
    svc_b.add_service_keys("svc", ["k1"], ["val2"])

    assert svc_a.get_service_all("svc") == {"k1": "val1"}
    assert svc_b.get_service_all("svc") == {"k1": "val2"}

    # Services are stored under their respective prefixes
    assert "svc" in svc_a.get_services()
    assert "svc" in svc_b.get_services()
