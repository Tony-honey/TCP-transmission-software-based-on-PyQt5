# TCP-transmission-software-based-on-PyQt5
This is a TCP transmission software based on PyQt5 design, and also my software course design.

## 具体功能
具体实现了服务器与客户端互发消息，文件下载与上传。
同时，某一方突然中断可以再次连接，具体表现为服务器保持监听；客户端利用定时器模拟监听。
由于没有租用服务器，因此只在本机以及同一局域网下测试过。
另外，在本工程中没有搭建数据库，因此下载资源暂时设定为服务器端选择一个文件夹路径作为下载源
