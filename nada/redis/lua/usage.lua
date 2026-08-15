#!lua name=request_usage

-- and howto do it: redis-cli -p 6389 -n 4 -x function load replace < usage.lua

local function set_usage(keys, args)
    local updated_at = redis.call('TIME')[1] .. "." .. redis.call('TIME')[2]
    local argoffset = 0
    local proc_count = 0
    -- Loop through keys and args
    for i = 1, #keys do
        local advert_id = keys[i]
        local pair_id = args[i + argoffset]
        local fiat_ad_price = args[i + argoffset + 1]
        local ass_id
        local fiat_id
        local cat_id
        -- TODO fix this, format code may be incorrect
        for cat, ass, fiat in string.gmatch(pair_id, "(%w+):(%w+):(%w+)") do
            cat_id = cat
            ass_id = ass
            fiat_id = fiat
        end
        -- add the flat collection
        local a = redis.call('ZADD', cat_id, fiat_ad_price, advert_id)
        -- add the per pair collection
        local b = redis.call('ZADD', pair_id, fiat_ad_price, advert_id)
        local j = string.format(
            '{"ID": "%s", "ASSET": "%s", "DTIME": %s, "PRICE": %s, "PX_ASSET": "%s", "CATEGORY": "%s"}', advert_id,
            ass_id,
            updated_at, fiat_ad_price, fiat_id, cat_id)
        local z = redis.call('SET', advert_id, j)
        argoffset = argoffset + 1
        proc_count = proc_count + 1
    end
    return proc_count
end

local function get_usage(keys, args)
    -- This is the set portion?
    -- Define some parms: one key for pair_id, reverse, min, max, limit, offset
    local pair_id = keys[1]
    -- everything else is args
    local low_to_high = (args[1] == 'true')
    local min_val = args[2] or 0
    -- TODO fix this with a system variable, max something, or simple zrange
    --  prices are already in the json values
    local max_val = args[3] or 999999999
    local rec_limit = args[4] or false
    local rec_offset = args[5] or 0
    local result = {}
    -- Get the price list, default is for sellers? zrangebyscore?
    local p_oper = 'ZRANGEBYSCORE'
    if low_to_high then
        p_oper = 'ZREVRANGEBYSCORE'
        low_to_high = max_val
        max_val = min_val
        min_val = low_to_high
    end
    local mp_keys = redis.call(p_oper, pair_id, min_val, max_val)
    local nprices = table.getn(mp_keys)
    if nprices == 0 then
        return nil
    end
    local result = redis.call('MGET', unpack(mp_keys))
    return result
end

redis.register_function('get_usage', get_usage)
redis.register_function('set_usage', set_usage)
