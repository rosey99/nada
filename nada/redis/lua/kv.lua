#!lua name=nada_kv


local function set_keys(keys, args)
    local updated_at = redis.call('TIME')[1] .. "." .. redis.call('TIME')[2]
    -- Loop through keys and args
    local all_keys_and_values = {}
    for i = 1, #keys do
        local kv_id
        local kv_store
        for a, b, c in string.gmatch(keys[i], "(%w+):(%w+):(%w+)") do
            kv_id = a
            kv_store = b
            local _ = c
        end
        -- add the flat collection
        local service_result = redis.call('SADD', kv_id, kv_store)
        local key_result = redis.call('SADD', kv_store, keys[i])
        table.insert(all_keys_and_values, keys[i])
        table.insert(all_keys_and_values, args[i])
    end
    return redis.call('MSET', unpack(all_keys_and_values))
end

local function remove_keys(keys, args)
    local updated_at = redis.call('TIME')[1] .. "." .. redis.call('TIME')[2]
    -- Loop through keys and args
    local all_key_stores = {}
    local kv_id
    local kv_store
    for i = 1, #keys do
        -- TODO fix this, format code may be incorrect
        for a, b, c in string.gmatch(keys[i], "(%w+):(%w+):(%w+)") do
            kv_id = a
            kv_store = b
            local _ = c
        end
        all_key_stores[kv_store] = kv_id
    end
    for k, v in pairs(all_key_stores) do
        local key_result = redis.call('SREM', k, unpack(keys))
        local keys_remaining = redis.call('SMEMBERS', k)
        if keys_remaining == nil then
            redis.call('SREM', v, k)
        end
    end
    local key_res = redis.call('DEL', unpack(keys))
    return key_res
end

redis.register_function('set_keys', set_keys)
redis.register_function('remove_keys', remove_keys)
