#!lua name=nada_kv


local function set_keys(keys, args)
    -- Loop through keys
    local all_keys_and_values = {}
    for i = 1, #keys do
        local kv_id
        local kv_store
        for a, b, c in string.gmatch(keys[i], "(%w+):(%w+):(%w+)") do
            kv_id = a
            kv_store = b
            local _ = c
        end
        -- add the sets, and allow for multiple KV instances
        redis.call('SADD', kv_id, kv_store)
        redis.call('SADD', kv_id .. ':' .. kv_store, keys[i])
        table.insert(all_keys_and_values, keys[i])
        table.insert(all_keys_and_values, args[i])
    end
    return redis.call('MSET', unpack(all_keys_and_values))
end

local function remove_keys(keys, args)
    -- Loop through keys and args
    local all_key_stores = {}
    local kv_id
    local kv_store
    for i = 1, #keys do
        for a, b, c in string.gmatch(keys[i], "(%w+):(%w+):(%w+)") do
            kv_id = a
            kv_store = b
            local _ = c
        end
        all_key_stores[kv_store] = kv_id
    end
    for k, v in pairs(all_key_stores) do
        local _ = redis.call('SREM', k, unpack(keys))
        local keys_remaining = redis.call('SMEMBERS', v .. ':' .. k)
        if #keys_remaining == 0 then
            redis.call('SREM', v, k)
        end
    end
    return redis.call('DEL', unpack(keys))
end

redis.register_function('set_keys', set_keys)
redis.register_function('remove_keys', remove_keys)
