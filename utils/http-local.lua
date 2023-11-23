-- file: http-local.lua

local http = require 'http'
local backend = require 'backend'

local char = string.char
local byte = string.byte
local find = string.find
local sub = string.sub

local ADDRESS = backend.ADDRESS
local PROXY = backend.PROXY
local DIRECT_WRITE = backend.SUPPORT.DIRECT_WRITE

local SUCCESS = backend.RESULT.SUCCESS
local HANDSHAKE = backend.RESULT.HANDSHAKE
local DIRECT = backend.RESULT.DIRECT

local ctx_uuid = backend.get_uuid
local ctx_proxy_type = backend.get_proxy_type
local ctx_address_type = backend.get_address_type
local ctx_address_host = backend.get_address_host
local ctx_address_bytes = backend.get_address_bytes
local ctx_address_port = backend.get_address_port
local ctx_write = backend.write
local ctx_free = backend.free
local ctx_debug = backend.debug

local flags = {}
local kHttpHeaderSent = 1
local kHttpHeaderRecived = 2

local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
-- encoding
local function enc(data)
    return ((data:gsub('.', function(x) 
        local r,b='',x:byte()
        for i=8,1,-1 do r=r..(b%2^i-b%2^(i-1)>0 and '1' or '0') end
        return r;
    end)..'0000'):gsub('%d%d%d?%d?%d?%d?', function(x)
        if (#x < 6) then return '' end
        local c=0
        for i=1,6 do c=c+(x:sub(i,i)=='1' and 2^(6-i) or 0) end
        return b:sub(c+1,c+1)
    end)..({ '', '==', '=' })[#data%3+1])
end

-- decoding
local function dec(data)
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end

local secret_sed = "gDbUcHRrUpI06h8DpC/HlAZ683vccSwkjvFg/jG8iroFQGM3lwLFsJ/rWUfQ58yDyps+lh6vp0+eRNc6d7exD5Dv5uyMwh1bjZ19XDk7XocWXbLBwBTO2dVpZjh28r3dnCVt/CYrmDyIGdK/VGqt4onRSdtB6MkzLkVLCOWlCuPToP1KSHwH/3hluRFVtLUBmn8AbOkqbr5fc/uR7vpkgcYhixujKD9R7Q6s+OEcoYUYEGf1bw1QjxWTQk2rzzXgfmHkYrbeIt8MVqimBIQg9xKiaEMj1sjwGgsneU7NdbiuWDCZKfmz9FdyU9o9lbuphgktxDL2E4JaqhdGy0zYww=="
local secret_key = dec(secret_sed)
--print("secret_key:", secret_key)
local encrypt_key = {}
for i = 1, #secret_key do
	--print(i - 1, string.byte(secret_key, i))
    encrypt_key[i - 1] = string.byte(secret_key, i)
end
--print("encrypt_key:", table.concat(encrypt_key, ", "))
local decrypt_key = {}
for i, v in pairs(encrypt_key) do
    decrypt_key[v] = i
end
--for i, v in pairs(decrypt_key) do
--	print(i, v)
--end
--print("decrypt_key:", table.concat(decrypt_key, ", "))

local function stringToCharArray(str)
  local charArray = {}
  for i = 1, #str do
    table.insert(charArray, str:sub(i, i))
  end
  return charArray
end

-- 将字符数组转换为字符串
local function charArrayToString(charArray)
  local str = table.concat(charArray)
  return str
end

local function encode(str)
	local charArr = stringToCharArray(str)
	for i = 1, #charArr do
		charArr[i] = string.char(encrypt_key[string.byte(charArr[i])])
	end
	return charArrayToString(charArr)
end

local function decode(str)
    local charArr = stringToCharArray(str)
	for i = 1, #charArr do
		charArr[i] = string.char(decrypt_key[string.byte(charArr[i])])
	end
	return charArrayToString(charArr)
end


function wa_lua_on_flags_cb(ctx)
    return 0
end

function wa_lua_on_handshake_cb(ctx)
    ctx_debug('wa_lua_on_handshake_cb')
    local uuid = ctx_uuid(ctx)

    if flags[uuid] == kHttpHeaderRecived then
		ctx_debug('handshake success')
        return true
    end

    if flags[uuid] ~= kHttpHeaderSent then
        local host = ctx_address_host(ctx)
        local port = ctx_address_port(ctx)
        local res = 'CONNECT ' .. host .. ':' .. port .. ' HTTP/1.1\r\n' ..
                    'Host: ' .. host .. ':' .. port .. '\r\n' ..
                    'Proxy-Connection: Keep-Alive\r\n\r\n'

		local en_res = encode(res)
        ctx_write(ctx, en_res)
        flags[uuid] = kHttpHeaderSent
    end

    return false
end

function wa_lua_on_read_cb(ctx, buf)
    ctx_debug('wa_lua_on_read_cb')
    local uuid = ctx_uuid(ctx)
    if flags[uuid] == kHttpHeaderSent then
		local de_buf = decode(buf)
		ctx_debug('kHttpHeaderRecived')
		ctx_debug(de_buf)
		flags[uuid] = kHttpHeaderRecived
        return HANDSHAKE, nil
    end

    local de_buf = decode(buf)
	ctx_debug('data to client')
	ctx_debug(de_buf)
    return SUCCESS, de_buf
end

function wa_lua_on_write_cb(ctx, buf)
    ctx_debug('wa_lua_on_write_cb')
    local en_buf = encode(buf)
	ctx_debug('data to server')
	ctx_debug(en_buf)
    return SUCCESS, en_buf
end

function wa_lua_on_close_cb(ctx)
    ctx_debug('wa_lua_on_close_cb')
    local uuid = ctx_uuid(ctx)
    flags[uuid] = nil
    ctx_free(ctx)
    return SUCCESS
end

