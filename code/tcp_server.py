import sys
import os
import images
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QDataStream, QFile, QFileInfo, Qt, QByteArray, QIODevice
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtNetwork import QTcpServer, QHostAddress
from PyQt5.QtWidgets import QApplication, QWidget, QTextBrowser, QMessageBox, \
    QProgressBar, QLabel, QTextEdit, QPushButton, QFileDialog
 
 
class Server(QWidget):
    def __init__(self):
        super(Server, self).__init__()
        self.setWindowTitle("服务端")
        self.setWindowIcon(QIcon(':/customer-service-2-line.png'))
        self.resize(1280, 905)
        self.setFixedSize(self.width(), self.height())
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(":/background3.jpeg")))
        self.setPalette(window_pale)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        # 1
        self.browser = QTextBrowser(self)
        self.edit = QTextEdit(self)
        self.browser.setFont(QFont("宋体",14,QFont.Normal))
        self.edit.setFont(QFont("宋体",14,QFont.Normal))
        self.browser.setGeometry(20,20,1240,550)
        self.edit.setGeometry(20,590,1240,200)
        self.browser.setStyleSheet("background:transparent;")
        self.edit.setStyleSheet("background:transparent;border-width:2;border-style:outset;")

        self.label = QLabel('传输进度条:', self)
        self.label.setFont(QFont("宋体",12,QFont.Bold))
        self.label.setStyleSheet("color:red;")
        self.label.setGeometry(20,860,110,30)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setGeometry(140,860,1120,30)

        self.send_btn = QPushButton('发送', self)
        self.send_btn.setEnabled(False)
        self.send_btn.setGeometry(1160,805,100,40)
        self.send_btn.setIcon(QIcon(":/send-plane-line.png"))
        self.send_btn.setFont(QFont("宋体",10,QFont.Normal))
 
 
        # 2
        self.server = QTcpServer(self)
        if not self.server.listen(QHostAddress.Any, 6666):
            self.browser.append(self.server.errorString())
        self.server.newConnection.connect(self.new_socket_slot)

        self.file_sock = QTcpServer(self)
        if not self.file_sock.listen(QHostAddress.Any, 6766):
            self.browser.append(self.file_sock.errorString())
        self.file_sock.newConnection.connect(self.file_sock_slot)

        self.file_download_sock = QTcpServer(self)
        if not self.file_download_sock.listen(QHostAddress.Any, 6866):
            self.browser.append(self.file_download_sock.errorString())
        self.file_download_sock.newConnection.connect(self.file_download_sock_slot)

        self.file_transfer_sock = QTcpServer(self)
        if not self.file_transfer_sock.listen(QHostAddress.Any, 6966):
            self.browser.append(self.file_transfer_sock.errorString())
        self.file_transfer_sock.newConnection.connect(self.file_transfer_sock_slot)
        
        self.file_peer_port = -1
        self.download_peer_port = -1
        self.server_peer_port = -1
        self.transfer_peer_port = -1

        self.edit.textChanged.connect(self.text_change_slot)

    def text_change_slot(self):
        message = self.edit.toPlainText()     
        if '\n' in message:     
            message = message.replace('\n','')            
            self.edit.setText(message)            
            self.write_data_slot()

    
    def file_sock_slot(self):
        self.totalBytesToReceive = 0  # 要接收的数据的总大小
        self.bytesReceived = 0  # 已接收的数据大小
        self.fileNameSize = 0  # 文件名长度
        self.flag = 000   #区分是否为文件夹
        self.counter = 0
        sock = self.file_sock.nextPendingConnection()
        peer_address = sock.peerAddress().toString()
        peer_port = sock.peerPort()
        self.file_peer_port = peer_port
        sock.readyRead.connect(lambda: self.read_file_slot(sock))
        sock.disconnected.connect(lambda: self.disconnected_slot(sock))
        self.file_sock.pauseAccepting()

    def file_download_sock_slot(self):
        sock = self.file_download_sock.nextPendingConnection()
        peer_address = sock.peerAddress().toString()
        peer_port = sock.peerPort()
        self.download_peer_port = peer_port
        self.download_file_slot(sock)
        sock.disconnected.connect(lambda: self.disconnected_slot(sock))
        sock.readyRead.connect(lambda: self.download_selection_slot(sock))
        self.file_download_sock.pauseAccepting()

    def file_transfer_sock_slot(self):
        self.transfer_sock = self.file_transfer_sock.nextPendingConnection()
        sock = self.transfer_sock
        peer_address = sock.peerAddress().toString()
        peer_port = sock.peerPort()
        self.transfer_peer_port = peer_port
        sock.disconnected.connect(lambda: self.disconnected_slot(sock))
        sock.bytesWritten.connect(lambda: self.sendData_slot(sock))
        self.file_download_sock.pauseAccepting()

    def new_socket_slot(self):
        sock = self.server.nextPendingConnection()
        self.server_sock = sock
        peer_address = sock.peerAddress().toString()
        self.server_peer_port = sock.peerPort()
        news = 'Connected with IP address {}, port {}'.format(peer_address, str(self.server_peer_port))
        self.browser.append(news)
        
        sock.readyRead.connect(lambda: self.read_data_slot(sock))
        sock.disconnected.connect(lambda: self.disconnected_slot(sock))
        self.server.pauseAccepting()
        self.send_btn.setEnabled(True)
        self.send_btn.clicked.connect(self.write_data_slot)    # 3

    def write_data_slot(self):
        message = self.edit.toPlainText()
        self.browser.append('Server: {}'.format(message))
        datagram = message.encode()
        self.server_sock.write(datagram)
        self.edit.clear()
    
    # 3
    def read_data_slot(self, sock):
        while sock.bytesAvailable():
            datagram = sock.read(sock.bytesAvailable())
            message = datagram.decode()
            self.browser.append('Client: {}'.format(message))

    def read_file_slot(self, sock):
        dataStream = QDataStream(sock)
        while sock.bytesAvailable():
            
        # 开始接收总字节数、文件名长度、文件名
            if self.bytesReceived <= 3:  # 接收到的数据小于sizeof(QInt64)*3，是刚开接收数据
                if sock.bytesAvailable() >= 3 and self.fileNameSize == 0:
                    self.totalBytesToReceive = dataStream.readInt64()
                    self.fileNameSize = dataStream.readInt64()
                    self.flag = dataStream.readInt64()
                    self.bytesReceived += 3
                    self.progress_bar.setValue(0)
                    if self.flag == 111:
                        QMessageBox.information(self, 'information', '文件夹接收成功')
                        sock.close()
                        self.file_sock.resumeAccepting()  # 重新开始接受新连接
                if sock.bytesAvailable() >= self.fileNameSize and self.fileNameSize != 0:
                    fileName = dataStream.readQString()
                    
                    self.bytesReceived += self.fileNameSize
                    if self.counter == 0:
                        self.dirpath = self.getUnrepeatSaveFilePath(os.getcwd(), fileName)
                        self.filePath = self.dirpath
                        if self.flag == 110:
                            news = '开始接收文件夹 {} ，保存路径为 {}'.format(fileName, self.dirpath)
                            self.browser.append(news)
                    else:
                        # 接收本地已有的同名文件时自动改名为不重复的文件路径
                        self.filePath = self.dirpath + fileName
                        
                    self.counter = 1
                    if int(self.flag/100) == 0:
                        self.toFile = QFile(self.filePath)
                        if not self.toFile.open(QFile.OpenModeFlag.WriteOnly):
                            QMessageBox.critical(self, 'Wrong', '无法打开文件')
                            return
                        self.info = QFileInfo(self.toFile)
                        self.recv_name = self.info.fileName()
                        if int(self.flag/10)%10 == 0:
                            news = '开始接收文件 {} ，保存路径为 {}'.format(self.recv_name, self.dirpath)
                            self.browser.append(news)
                    elif int(self.flag/100) == 1:
                        os.mkdir(self.filePath)  
                else:
                    return
                        
            # 开始接收文件二进制数据流
            if self.bytesReceived < self.totalBytesToReceive and int(self.flag/100) == 0:  # 已接收的数据小于总数据，写入文件
                self.progress_bar.setValue(0)
                received = self.bytesReceived
                self.bytesReceived += min(self.totalBytesToReceive-self.bytesReceived, sock.bytesAvailable())
                bytes_obj = sock.read(min(self.totalBytesToReceive-received, sock.bytesAvailable()))
                qbyte = QByteArray(bytes_obj)
                self.toFile.write(qbyte)
                self.progress_bar.setValue(int(self.bytesReceived * 100 / self.totalBytesToReceive))

            # 接收完毕
            if self.bytesReceived == self.totalBytesToReceive:
                if self.flag == 10:
                    self.toFile.close()
                elif self.flag == 000:
                    self.toFile.close()
                    sock.close()
                    QMessageBox.information(self, 'information', '文件接收成功')
                    self.file_sock.resumeAccepting()  # 重新开始接受新连接
                if int(self.flag/10)%10 == 1:
                    self.bytesReceived = 0
                    self.fileNameSize = 0
    
    def getUnrepeatSaveFilePath(self, dirPath, fileName):
        '''获取不重复的文件路径'''
        filePath = os.path.join(dirPath, fileName)
        if os.path.exists(filePath):
            fileNameTxt, ext = os.path.splitext(fileName)
            for i in range(2, 31):
                filePath = os.path.join(dirPath, '%s(%s)%s' % (fileNameTxt, i, ext))
                if not os.path.exists(filePath):
                    return filePath
            # 如果fileName2~30都存在，删掉fileName30并返回fileName30
            try:
                os.remove(filePath)
            except BaseException:
                pass
            return filePath
        else:
            return filePath

    def download_file_slot(self, sock):
        self.folder = QFileDialog(self)
        self.download_path = self.folder.getExistingDirectory(self, "选择一个文件夹作为客户端下载资源", os.getcwd())
        for path, dirnames, filenames in os.walk(self.download_path):
            self.dir_name_list = []
            self.file_name_list = []
            self.dir_path_list = []
            self.file_path_list = []
            for dirname in dirnames:
                self.dir_name_list.append(dirname)
                dir_path = os.path.join(path, dirname)
                self.dir_path_list.append(dir_path)
                message = dirname + "/"
                datagram = message.encode()
                sock.write(datagram)

            for filename in filenames:
                self.file_name_list.append(filename)
                file_path = os.path.join(path, filename)
                self.file_path_list.append(file_path)
                message = filename + "/"
                datagram = message.encode()
                sock.write(datagram)

            break

    def download_selection_slot(self, sock):
        while sock.bytesAvailable():
            datagram_temp = sock.read(sock.bytesAvailable()).decode()
            datagram = int(datagram_temp)
            if datagram < len(self.dir_name_list):
                self.browser.append('Server: 需要下载的文件夹名称 {}'.format(self.dir_name_list[datagram]))
                self.download_folder(self.dir_name_list[datagram], self.dir_path_list[datagram])
            elif datagram < len(self.dir_name_list) + len(self.file_name_list):
                self.browser.append('Server: 需要下载的文件名称 {}'.format(self.file_name_list[datagram-len(self.dir_name_list)]))
                self.download_file(self.file_name_list[datagram-len(self.dir_name_list)], self.file_path_list[datagram-len(self.dir_name_list)])

    def download_folder(self, foldername, dirpath):
        self.name_list = []
        self.path_list = []
        self.info = QFileInfo(dirpath)
        self.folder_name = self.info.fileName()

        cnt = 0
        for path, dirnames, filenames in os.walk(dirpath):
            fpath = path.replace(dirpath, '')
            if len(dirnames) == 0 and len(filenames) == 0 and cnt == 0:
                self.null_flag = 1
            else:
                self.null_flag = 0
            cnt += 1
            for filename in filenames:
                self.name = fpath + "\\" + filename
                self.name_list.append(self.name)
                self.file_path = path + "\\" + filename
                self.path_list.append(self.file_path)
                self.info_folder_file = QFileInfo(self.file_path)

   
        self.download_flag = 110   # flag中的第一位表示发送文件夹或文件，第二位标记是文件夹中的文件还是单独发送文件
                            # 第三位表示文件夹是否遍历完成    
        self.folder_deal_slot(foldername, dirpath, self.transfer_sock)   

    def download_file(self, filename, filepath):
        self.download_file_path = filepath
        self.download_name = filename
        self.file_deal_slot(self.transfer_sock)       

    def file_deal_slot(self, sock):
        #打开文件
        self.download_flag = 000
        self.filep = QFile(self.download_file_path)
        if not self.filep.open(QFile.OpenModeFlag.ReadOnly):
            QMessageBox.critical(self, 'Wrong', '文件打开失败')
            return
        else:
            self.file_header_slot(sock)

         

    def folder_deal_slot(self, foldername, dirpath, sock):
        
        self.download_flag = 110
        self.download_name = foldername
        self.download_folder_path = dirpath
        self.file_header_slot(sock)
        for path, dirnames, filenames in os.walk(self.download_folder_path):
            fpath = path.replace(self.download_folder_path, '')
            for dirname in dirnames:
                self.download_flag = 110
                self.download_name = fpath + "\\" + dirname
                self.file_header_slot(sock)

        self.index = 0   

    def folder_file_header(self, sock):
        self.download_flag = 10
        
        #打开文件
        self.filep = QFile(self.path_list[self.index])
        if not self.filep.open(QFile.OpenModeFlag.ReadOnly):
            QMessageBox.critical(self, 'Wrong', '文件打开失败')
            return
        self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
        dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
        dataStream.setVersion(dataStream.Version.Qt_5_15)
        self.totalBytesToSend = self.filep.size()
        
        dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
        dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
        dataStream.writeInt64(self.download_flag)  # 区分是否为文件夹,1表示文件夹
        dataStream.writeQString(self.name_list[self.index])  # 文件名
        self.totalBytesToSend += self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
        self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
        dataStream.device().seek(0)
        dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
        dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
        self.bytesToWrite = self.totalBytesToSend - sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小

    def file_header_slot(self, sock):
        
        if self.download_flag == 0:
            self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
            dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
            dataStream.setVersion(dataStream.Version.Qt_5_15)
            self.totalBytesToSend = self.filep.size()
            
            dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
            dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
            dataStream.writeInt64(self.download_flag)  # 区分是否为文件夹,1表示文件夹
            dataStream.writeQString(self.download_name)  # 文件名
             
            self.totalBytesToSend += self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
            self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
            dataStream.device().seek(0)
            dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
            dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
            self.bytesToWrite = self.totalBytesToSend - sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小
            # self.bytesBuff.resize(0)
        elif int(self.download_flag/100) == 1:
            self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
            dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
            dataStream.setVersion(dataStream.Version.Qt_5_15)
            dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
            dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
            dataStream.writeInt64(self.download_flag)  # 占位，区分是否为文件夹,1表示文件夹
            if self.download_flag != 111:
                dataStream.writeQString(self.download_name)  # 文件夹名

            self.totalBytesToSend = self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
            self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
            dataStream.device().seek(0)
            dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
            if self.download_flag != 111:
                dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
            self.bytesToWrite = self.totalBytesToSend - sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小
            self.bytesBuff.resize(0)
            

    def sendData_slot(self, sock):
        buffsize = 64*1024
        if self.bytesToWrite > 0:
            self.bytesBuff = self.filep.read(min(self.bytesToWrite, buffsize))  # 每次最多发送buffsize的数据
            self.bytesToWrite -= sock.write(self.bytesBuff)
            #self.bytesBuff.resize(0)
            self.progress_bar.setValue(int((self.totalBytesToSend - self.bytesToWrite) * 100 / self.totalBytesToSend))
        else:    
            if self.download_flag == 000:  # 单独发送文件完成
                self.filep.close()
                QMessageBox.information(self, 'information', '文件发送成功')
                sock.close()
                self.file_transfer_sock.resumeAccepting()
            elif self.download_flag == 10:
                sock.flush()
                self.index += 1
                if self.index < len(self.name_list):
                    self.folder_file_header(sock)
                else:
                    self.index = 0
                    self.download_flag = 111 # 结束
                    self.file_header_slot(sock)
            elif self.download_flag == 110:
                if self.null_flag == 1:
                    self.index = 0
                    self.download_flag = 111 # 结束
                    self.file_header_slot(sock)
                else:
                    self.folder_file_header(sock)
            elif self.download_flag == 111:
                QMessageBox.information(self, 'information', '文件夹发送成功')
                sock.close()
                self.file_transfer_sock.resumeAccepting()

    def disconnected_slot(self, sock):
        peer_address = sock.peerAddress().toString()
        peer_port = sock.peerPort()
        sock.close()

        if peer_port == self.server_peer_port:
            news = 'Disconnected with IP address {}, port {}'.format(peer_address, str(peer_port))
            self.browser.append(news)
            self.server.resumeAccepting()
            
        
        if peer_port == self.file_peer_port:
            self.file_sock.resumeAccepting()
    
        if peer_port == self.download_peer_port:
            self.file_download_sock.resumeAccepting()
    
        if peer_port == self.transfer_peer_port:
            self.file_transfer_sock.resumeAccepting()

 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Server()
    demo.show()
    sys.exit(app.exec_())
