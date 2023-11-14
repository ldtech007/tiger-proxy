# tiger-proxy

## 介绍

之前用c语言写了一个http代理ldproxy，写的过程顺便熟悉了一下socket、epoll的使用，数据仅使用了@gwuhaolin的简单混淆算法，没有加密，由于比较小众，还是比较稳定的。在使用的过程中，发现ldproxy存在内存泄漏的问题，c语言很容易写出各种内存问题，也懒得去查了，直接用python重新实现了一个http代理，顺便也实现了一个socks5代理。实现用到了python的高效异步io库asyncio，数据也是仅做了混淆。为了充分利用cpu，服务端的进程数和cpu个数保持一致（没有做强绑定，还是CPU自动来调度）。

## 使用方法

1. 安装python，保证版本>=3.7.1

2. 目录utils中的generate_key用来生成secret_sed，用新生成的secret_sed替换代码中的secret_sed变量的值，保证密钥的安全性。

```
cd utils
python generate_key.py
```
3. 可以直接修改代码替换server和client监听的地址和端口。

4. 运行服务端，在vps上运行http-server.py 或 socks-server.py

```
cd http-proxy
python http-server.py
或
cd socks-proxy
python socks-server.py
```
5. 运行客户端

```
cd http-proxy
python http-client.py
或
cd socks-proxy
python socks-client.py
```

## 其他

还有一些可以完善的，比如secret_sed、ip、port等从代码里抽出来放到配置文件中，增加用户认证的逻辑，支持ipv6等。有兴趣的同学可以参与进来，提交你的代码。

在普通的pc和linux虚拟机中速度还是很快的，在嵌入式设备上cpu对python的支持就没那么好了，嵌入式设备的cpu对python的解释比较慢，也不建议大家在嵌入式设备上运行。
