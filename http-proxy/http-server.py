import asyncio
import logging
import base64
import multiprocessing
import socket
import platform
#import traceback

#logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
#                    level=logging.DEBUG)

""" logging.basicConfig(level=logging.DEBUG,#控制台打印的日志级别
                    filename='client.log',
                    filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    #a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    #日志格式
                    ) """

# generate_key生成的密钥 
secret_sed = "gDbUcHRrUpI06h8DpC/HlAZ683vccSwkjvFg/jG8iroFQGM3lwLFsJ/rWUfQ58yDyps+lh6vp0+eRNc6d7exD5Dv5uyMwh1bjZ19XDk7XocWXbLBwBTO2dVpZjh28r3dnCVt/CYrmDyIGdK/VGqt4onRSdtB6MkzLkVLCOWlCuPToP1KSHwH/3hluRFVtLUBmn8AbOkqbr5fc/uR7vpkgcYhixujKD9R7Q6s+OEcoYUYEGf1bw1QjxWTQk2rzzXgfmHkYrbeIt8MVqimBIQg9xKiaEMj1sjwGgsneU7NdbiuWDCZKfmz9FdyU9o9lbuphgktxDL2E4JaqhdGy0zYww=="
encrypt_key = bytearray(base64.b64decode(secret_sed))
decrypt_key = encrypt_key.copy()
for i, v in enumerate(encrypt_key):
    decrypt_key[v] = i

def encode(data: bytearray):
    for i, v in enumerate(data):
        data[i] = encrypt_key[v]

def decode(data: bytearray):
    for i, v in enumerate(data):
        data[i] = decrypt_key[v]

async def handle_client(reader, writer):
    try:
       # 读取客户端请求头
        headers_data = b''
        #while True:
        chunk = bytearray(await reader.read(8192)) # 读取固定长度的数据
        decode(chunk)
        headers_data += bytes(chunk)
        if b'\r\n\r\n' not in headers_data:
            return

        headers, body_data = headers_data.split(b'\r\n\r\n', 1)
        headers = headers.decode().split('\r\n')

        logging.debug("headers: %s\n", headers)
        logging.debug("body_data: %s\n", body_data)

        # 解析请求头
        method, path, version = headers[0].split(' ')

        headers_dict = {}
        for header in headers[1:]:
            key, value = header.split(':', 1)
            headers_dict[key.strip()] = value.strip()

        logging.debug("headers_dict: %s\n", headers_dict)
        hosts = headers_dict['Host'].split(':')

        if method == 'CONNECT':
            host = hosts[0]
            if len(hosts) == 1:
                port = '443'
            else:
                port = hosts[1]
            # 处理CONNECT请求
            remote_reader, remote_writer = await asyncio.open_connection(host, port)
            resp = bytearray(b'HTTP/1.1 200 Connection established\r\n\r\n')
            encode(resp)
            writer.write(bytes(resp))
            await writer.drain()
             # 创建两个任务，分别进行双向数据转发
            tasks = [
                asyncio.create_task(forward_to_server(reader, remote_writer)),
                asyncio.create_task(forward_to_client(remote_reader, writer))
            ]
            
            # 等待任务完成
            await asyncio.gather(*tasks)

        else:
            logging.debug("http proxy\n")
            host = hosts[0]
            if len(hosts) == 1:
                port = '80'
            else:
                port = hosts[1]
            # 处理其他请求
            remote_reader, remote_writer = await asyncio.open_connection(host, port)
            remote_writer.write(headers_data)
            await writer.drain()
             # 创建两个任务，分别进行双向数据转发
            tasks = [
                asyncio.create_task(forward_to_server(reader, remote_writer)),
                asyncio.create_task(forward_to_client(remote_reader, writer))
            ]
            
            # 等待任务完成
            await asyncio.gather(*tasks)
    except Exception as e:
        #traceback.print_tb(e.__traceback__)
        # 处理异常
        logging.debug(f"Error: {e}")
        writer.close()

# 进行数据转发
async def forward_to_server(src, dst):

    try:
        while True: 
            data = await src.read(4096)
            if len(data) == 0:
                logging.debug("client已关闭")
                break
            logging.debug("datalen:%d, data: %s", len(data), data)
            data_array = bytearray(data)
            decode(data_array)
            dst.write(bytes(data_array))
            logging.debug("datalen:%d, data_array: %s", len(data_array), data_array)
            await dst.drain()
    except Exception as e:
        #traceback.print_tb(e.__traceback__)
        # 处理异常
        logging.debug(f"Error: {e}")
    finally:
        logging.debug("关闭server")
        dst.close()

# 进行数据转发
async def forward_to_client(src, dst):

    try:
        while True: 
            data = await src.read(4096)
            if len(data) == 0:
                logging.debug("server已关闭")
                break
            logging.debug("datalen:%d, data: %s", len(data), data)
            data_array = bytearray(data)
            encode(data_array)
            dst.write(bytes(data_array))
            logging.debug("datalen:%d, data_array: %s", len(data_array), data_array)
            await dst.drain()
    except Exception as e:
        #traceback.print_tb(e.__traceback__)
        # 处理异常
        logging.debug(f"Error: {e}")
    finally:
        logging.debug("关闭client")
        dst.close()

def start_server():
    loop = asyncio.get_event_loop()
    async def run_server():
        # 创建一个套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置 SO_REUSEADDR 和 SO_REUSEPORT 属性
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if platform.system().lower() != 'windows':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # 绑定套接字到指定地址和端口
        sock.bind(('10.10.88.88', 8888))

        server = await asyncio.start_server(handle_client, sock=sock)
        # 进入事件循环
        async with server:
            await server.serve_forever()

    loop.run_until_complete(run_server())

if __name__ == '__main__':
    logging.info("服务启动...")
    
    # 创建多个子进程
    num_processes = multiprocessing.cpu_count()
    processes = []
    for _ in range(num_processes):
        process = multiprocessing.Process(target=start_server)
        process.start()
        processes.append(process)

    # 等待所有子进程结束
    for process in processes:
        process.join()