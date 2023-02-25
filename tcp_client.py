import sys
import re
import os
import images
import time
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QFileInfo, QFile, QByteArray, QDataStream, QIODevice, QTimer
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon, QFont
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtWidgets import QApplication, QWidget, QTextBrowser, QTextEdit, QPushButton, \
                            QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QDialog, QMessageBox, \
                            QTableView, QFileDialog, QProgressBar, QComboBox
 
class Client_Enter(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(592, 442)
        self.setWindowTitle("设置服务器IP")
        self.setWindowIcon(QIcon(':/user-line.png'))
        self.setFixedSize(self.width(), self.height())
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(":/background.jpg")))
        self.setPalette(window_pale)
        self.ip_label = QLabel('IP地址:', self)
        self.ip_label.setFont(QFont("msyh",12,QFont.Bold))
        self.ip_label.setGeometry(96,50,100,50)
        self.ip_line = QLineEdit(self)
        self.ip_line.setFont(QFont("msyh",12,QFont.Bold))
        self.ip_line.setGeometry(196, 50, 300, 50)
        self.ip_line.setClearButtonEnabled(True)
        self.sure_button = QPushButton('确认', self)
        self.sure_button.setGeometry(246, 380, 100, 50)
        self.sure_button.setFont(QFont("msyh",12,QFont.Normal))

        self.pushbutton_init()
        self.line_edit_init()
        

    def pushbutton_init(self):
        self.sure_button.setEnabled(False)
        self.sure_button.clicked.connect(self.check_func)
    
    def line_edit_init(self):
        self.ip_line.setPlaceholderText('请输入服务器IP地址')

        self.ip_line.textChanged.connect(self.check_input_func)

    def check_input_func(self):
        if self.ip_line.text():
            self.sure_button.setEnabled(True)
        else:
            self.sure_button.setEnabled(False)    
    
    def keyPressEvent(self, QKeyEvent):  # 键盘某个键被按下时调用
        #参数1  控件
        if QKeyEvent.key()== Qt.Key_Return:  #判断是否按下了回车
            self.check_func()

    def check_func(self):
        #利用正则表达式判断IP是否正确
        try:
            compile_ip=re.compile('^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')           
            if compile_ip.match(self.ip_line.text()): 
                ip = self.ip_line.text()
                port = 6666
                self.client = Client(self,ip, port)
                self.hide()
                self.client.exec_()  
                self.ip_line.clear()   
            else:    
                QMessageBox.information(self, 'Wrong', 'IP地址输入错误!')
                self.ip_line.clear()
        except:
            QMessageBox.information(self, 'Wrong', 'IP地址输入错误!')
            self.ip_line.clear()

        
class Client(QDialog):
    def __init__(self, mainWindow,ip, port):
        super(Client, self).__init__()
        # 1
        self.setWindowTitle("客户端")
        self.setWindowIcon(QIcon(':/message-3-line.png'))
        self.resize(1280, 905)
        self.setFixedSize(self.width(), self.height())
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(":/background3.jpeg")))
        self.setPalette(window_pale)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.ip = ip
        self.port = port
        self.mainWindow = mainWindow
        self.browser = QTextBrowser(self)
        self.edit = QTextEdit(self)
        self.browser.setFont(QFont("宋体",14,QFont.Normal))
        self.edit.setFont(QFont("宋体",14,QFont.Normal))
        self.browser.setGeometry(20,20,1240,550)
        self.edit.setGeometry(20,630,1240,200)
        self.browser.setStyleSheet("background:transparent;")
        self.edit.setStyleSheet("background:transparent;border-width:2;border-style:outset;")
        self.file_send_btn = QPushButton('上传文件', self)
        self.file_download_btn = QPushButton('下载文件', self)
        self.file_send_btn.setIcon(QIcon("upload-cloud-2-line.png"))
        self.file_download_btn.setIcon(QIcon("download-cloud-2-line.png"))
        self.file_send_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.file_download_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.file_send_btn.setGeometry(20,580,100,40)
        self.file_download_btn.setGeometry(140,580,100,40)
        self.file_send_btn.setLayoutDirection(Qt.LeftToRight)
        self.file_download_btn.setLayoutDirection(Qt.LeftToRight)
        
        self.send_btn = QPushButton('发送', self)
        self.send_btn.setEnabled(False)
        self.close_btn = QPushButton('清空', self)
        self.close_btn.setIcon(QIcon(":/close-circle-line.png"))
        self.send_btn.setIcon(QIcon(":/send-plane-line.png"))
        self.send_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.close_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.close_btn.setGeometry(1040,840,100,40)
        self.send_btn.setGeometry(1160,840,100,40)

        self.new_btn = QPushButton('重新输入IP', self)
        self.new_btn.setIcon(QIcon("':/user-line.png'"))
        self.new_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.new_btn.setGeometry(20,840,200,40)

        self.timer = QTimer(self)
        self.sock = QTcpSocket(self)
        self.shut_flag = 0
        self.cnt = 0
        self.connect_tcp()
        self.signal_init()

    def connect_tcp(self):
        self.sock.connectToHost(self.ip, self.port)
        self.sock.disconnected.connect(lambda: self.disconnected_slot(self.sock))     

    def disconnected_slot(self, sock):
        peer_address = sock.peerAddress().toString()
        peer_port = sock.peerPort()
        sock.close()
        if self.cnt == 0:
            news = 'IP为{}的服务器已断开！'.format(peer_address)
            self.browser.append(news)
            self.cnt = 1
        if self.shut_flag == 0:
            self.timer.start(100)
            self.timer.timeout.connect(self.connect_tcp)
     
    def signal_init(self):
        self.new_btn.clicked.connect(self.new_slot)
        self.close_btn.clicked.connect(self.close_slot)        # 4
        self.file_send_btn.clicked.connect(self.file_slot)
        self.file_download_btn.clicked.connect(self.file_download_slot)
        self.sock.connected.connect(self.connected_slot)       # 5
        self.sock.readyRead.connect(self.read_data_slot)       # 6
        self.edit.textChanged.connect(self.text_change_slot)

    def new_slot(self):
        self.close()
        self.mainWindow.show()
        
    def text_change_slot(self):
        message = self.edit.toPlainText()     
        if '\n' in message:     
            message = message.replace('\n','')   
            if len(message) != 0:         
                self.edit.setText(message)            
                self.write_data_slot() 
            else:
                self.edit.clear()
             
    def write_data_slot(self):
        message = self.edit.toPlainText()                 
        if len(message) != 0:
            self.browser.append('Client: {}'.format(message))
            datagram = message.encode()
            self.sock.write(datagram)
            self.edit.clear()
 
    def connected_slot(self):
        if self.timer.isActive():
            self.timer.stop()
            self.cnt = 0
        message = 'Connected! Ready to chat!'
        self.browser.append(message)
        self.send_btn.setEnabled(True)
        self.send_btn.clicked.connect(self.write_data_slot)    # 3
 
    def read_data_slot(self):
        while self.sock.bytesAvailable():
            datagram = self.sock.read(self.sock.bytesAvailable())
            message = datagram.decode()
            self.browser.append('Server: {}'.format(message))
 
    def close_slot(self):
        self.edit.clear()
    
    def file_slot(self):
        self.file = File_send(self.ip, self.port)
        self.file.exec_()

    def file_download_slot(self):
        self.download = File_download(self.ip, self.port)
        self.download.exec_()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Warning', '确认退出？', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.shut_flag = 1
            self.sock.close()
            event.accept()   
        else:
            event.ignore()


class File_send(QDialog):
    def __init__(self, ip, port):
        super(File_send, self).__init__()
        self.setWindowTitle("上传文件")
        self.setWindowIcon(QIcon(':/chat-upload-line.png'))
        self.resize(1280, 720)
        self.setFixedSize(self.width(), self.height())
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(":/background4.jpeg")))
        self.setPalette(window_pale)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.cwd = os.getcwd()
        self.flag = 0   #0表示传输文件，1表示传输文件夹
        self.ip = ip
        self.port = port
        self.select_file_btn = QPushButton('选择文件', self)
        self.select_folder_btn = QPushButton('选择文件夹', self)
        self.send_btn = QPushButton('上传文件', self)
        self.send_btn.setEnabled(False)
        self.send_folder_btn = QPushButton('上传文件夹', self)
        self.send_folder_btn.setEnabled(False)
        self.select_file_btn.setIcon(QIcon(":/file-line.png"))
        self.select_folder_btn.setIcon(QIcon(":/folder-line.png"))
        self.select_file_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.select_folder_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.select_file_btn.setGeometry(20,20,600,40)
        self.select_folder_btn.setGeometry(640,20,600,40)
        self.select_file_btn.setLayoutDirection(Qt.LeftToRight)
        self.select_folder_btn.setLayoutDirection(Qt.LeftToRight)
        self.send_btn.setIcon(QIcon(":/file-line.png"))
        self.send_folder_btn.setIcon(QIcon(":/folder-line.png"))
        self.send_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.send_folder_btn.setFont(QFont("宋体",10,QFont.Normal))
        self.send_btn.setGeometry(20,660,600,40)
        self.send_folder_btn.setGeometry(640,660,600,40)
        self.send_btn.setLayoutDirection(Qt.LeftToRight)
        self.send_folder_btn.setLayoutDirection(Qt.LeftToRight)

        self.label = QLabel('传输进度条:', self)
        self.label.setFont(QFont("宋体",12,QFont.Bold))
        self.label.setStyleSheet("color:red;")      #设置颜色
        self.label.setGeometry(20,610,110,30)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setGeometry(140,610,1120,30)

        self.model = QStandardItemModel(2,3,self)
        item = QStandardItem('文件名')
        self.model.setItem(0,0,item)
        item = QStandardItem('路径')
        self.model.setItem(0,2,item)
        item = QStandardItem('文件大小')
        self.model.setItem(0,1,item)

        self.table = QTableView(self)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().resizeSection(0, 150)
        self.table.setGeometry(20,80,1240,510)
        self.table.setFont(QFont("宋体",12,QFont.Bold))
        self.table.setStyleSheet("background:transparent;border-width:0;border-style:outset;")

        self.select_file_btn.clicked.connect(self.file_select_slot)
        self.select_folder_btn.clicked.connect(self.file_foder_select_slot)
        self.send_btn.clicked.connect(self.file_deal_sock_slot)
        self.send_folder_btn.clicked.connect(self.folder_deal_slot)

        self.shut_flag = 0


    def file_select_slot(self):
        try:
            self.file = QFileDialog(self)
            self.file_path, file_type = self.file.getOpenFileName(self, "选择文件", self.cwd)
            if len(self.file_path) == 0:
                QMessageBox.critical(self, 'Wrong', '文件选择失败')
            else:
                self.info = QFileInfo(self.file_path)
                #显示到表格
                self.file_name = self.info.fileName()
                self.name = self.file_name
                item = QStandardItem('{}'.format(self.file_name))
                self.model.setItem(1,0,item)
                item = QStandardItem('{}'.format(self.file_path))
                self.model.setItem(1,2,item)
                self.file_size = self.info.size()
                item = QStandardItem('{}'.format(round(self.file_size/1024/1024, 6)) + 'MB')
                self.model.setItem(1,1,item)

                self.progress_bar.setValue(0)  
                self.send_btn.setEnabled(True) 

                self.flag = 000 
                self.shut_flag = 0
        except:
            pass

    def file_foder_select_slot(self):
        try:
            self.folder = QFileDialog(self)
            self.folder_path = self.folder.getExistingDirectory(self, "选择文件夹", self.cwd)
            if len(self.folder_path) == 0:
                QMessageBox.critical(self, 'Wrong', '文件夹选择失败')
            else:
                self.name_list = []
                self.path_list = []
                self.info = QFileInfo(self.folder_path)
                #显示到表格
                self.folder_name = self.info.fileName()
                item = QStandardItem('{}'.format(self.folder_name))
                self.model.setItem(1,0,item)
                item = QStandardItem('{}'.format(self.folder_path))
                self.model.setItem(1,2,item)
                self.folder_size = 0
                for path, dirnames, filenames in os.walk(self.folder_path):
                    fpath = path.replace(self.folder_path, '')
                        
                    for filename in filenames:
                        self.name = fpath + "\\" + filename
                        self.name_list.append(self.name)
                        self.file_path = path + "\\" + filename
                        self.path_list.append(self.file_path)
                        self.info_folder_file = QFileInfo(self.file_path)
                        self.folder_size += self.info_folder_file.size()

                item = QStandardItem('{}'.format(round(self.folder_size/1024/1024,6)) + 'MB')
                self.model.setItem(1,1,item)

                self.progress_bar.setValue(0)
                self.send_folder_btn.setEnabled(True)    
                self.flag = 110   # flag中的第一位表示发送文件夹或文件，第二位标记是文件夹中的文件还是单独发送文件
                                  # 第三位表示文件夹是否遍历完成   
                self.shut_flag = 0           
        except:
            pass

    def disconnect_slot(self):
        self.file_sock.close()
        if self.shut_flag == 0:     #停止传输
            QMessageBox.information(self, 'information', '服务器异常关闭')
            self.progress_bar.setValue(0)

    def file_deal_sock_slot(self):
        self.file_sock = QTcpSocket()
        self.file_sock.abort()
        self.file_sock.connectToHost(self.ip, self.port+100)
        self.file_sock.bytesWritten.connect(self.sendData_slot)
        self.file_sock.disconnected.connect(self.disconnect_slot)
        self.file_deal_slot()

    def file_deal_slot(self):
        #打开文件
        self.filep = QFile(self.file_path)
        if not self.filep.open(QFile.OpenModeFlag.ReadOnly):
            QMessageBox.critical(self, 'Wrong', '文件打开失败')
            self.send_btn.setEnabled(False)
            return
        else:
            self.send_btn.setEnabled(False)
            self.file_header_slot()     

    def folder_deal_slot(self):
        self.file_sock = QTcpSocket()
        self.file_sock.abort()
        self.file_sock.connectToHost(self.ip, self.port+100)
        self.file_sock.bytesWritten.connect(self.sendData_slot)
        self.file_sock.disconnected.connect(self.disconnect_slot)
        self.flag = 110
        self.name = self.folder_name
        self.file_header_slot()
        for path, dirnames, filenames in os.walk(self.folder_path):
            fpath = path.replace(self.folder_path, '')
            
            for dirname in dirnames:
                self.flag = 110
                self.name = fpath + "\\" + dirname
                self.file_header_slot()
        if len(filenames) == 0:
            self.null_flag = 1
        else:
            self.null_flag = 0
        self.index = 0   

    def folder_file_header(self):
        self.flag = 10
        #打开文件
        self.filep = QFile(self.path_list[self.index])
        if not self.filep.open(QFile.OpenModeFlag.ReadOnly):
            QMessageBox.critical(self, 'Wrong', '文件打开失败')
            self.send_btn.setEnabled(False)
            return
        self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
        dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
        dataStream.setVersion(dataStream.Version.Qt_5_15)
        self.totalBytesToSend = self.filep.size()
        
        dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
        dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
        dataStream.writeInt64(self.flag)  # 区分是否为文件夹,1表示文件夹
        dataStream.writeQString(self.name_list[self.index])  # 文件名
        self.totalBytesToSend += self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
        self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
        dataStream.device().seek(0)
        dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
        dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
        self.bytesToWrite = self.totalBytesToSend - self.file_sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小

    def file_header_slot(self):
        
        if self.flag == 0:
            self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
            dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
            dataStream.setVersion(dataStream.Version.Qt_5_15)
            self.totalBytesToSend = self.filep.size()
            
            dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
            dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
            dataStream.writeInt64(self.flag)  # 区分是否为文件夹,1表示文件夹
            dataStream.writeQString(self.name)  # 文件名
             
            self.totalBytesToSend += self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
            self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
            dataStream.device().seek(0)
            dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
            dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
            self.bytesToWrite = self.totalBytesToSend - self.file_sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小
            # self.bytesBuff.resize(0)
        elif int(self.flag/100) == 1:
            self.bytesBuff = QByteArray()  # 数据缓冲区，存放要发送的数据
            dataStream = QDataStream(self.bytesBuff, QIODevice.OpenModeFlag.WriteOnly)  # 序列化的编码二进制流
            dataStream.setVersion(dataStream.Version.Qt_5_15)
            dataStream.writeInt64(0)  # 要发送的总字节数（占位），sizeof(QInt64)=1
            dataStream.writeInt64(0)  # 文件名长度（占位），sizeof(QInt64)=1
            dataStream.writeInt64(self.flag)  # 占位，区分是否为文件夹,1表示文件夹
            if self.flag != 111:
                dataStream.writeQString(self.name)  # 文件夹名

            self.totalBytesToSend = self.bytesBuff.size()  # 要发送的总字节数=文件的二进制数据流总大小+QInt64字节数+QInt64字节数+文件名长度
            self.progress_bar.setValue(0)  # 最大值范围(-2147483648,2147483647),改成(0,100)
            dataStream.device().seek(0)
            dataStream.writeInt64(self.totalBytesToSend)  # 要发送的总字节数
            if self.flag != 111:
                dataStream.writeInt64(self.bytesBuff.size() - 3)  # 文件名长度=数据缓冲区大小-sizeof(QInt64)*3
            self.bytesToWrite = self.totalBytesToSend - self.file_sock.write(self.bytesBuff)  # 剩余要发送的数据大小，即文件实际内容的大小
            self.bytesBuff.resize(0)
            

    def sendData_slot(self):
        buffsize = 64*1024
        if self.bytesToWrite > 0:
            self.send_btn.setEnabled(False)
            self.bytesBuff = self.filep.read(min(self.bytesToWrite, buffsize))  # 每次最多发送buffsize的数据
            self.bytesToWrite -= self.file_sock.write(self.bytesBuff)
            self.progress_bar.setValue(int((self.totalBytesToSend - self.bytesToWrite) * 100 / self.totalBytesToSend))
        else:    
            if self.flag == 000:  # 单独发送文件完成
                self.filep.close()
                # self.file_sock.close()
                self.send_btn.setEnabled(False)
                self.shut_flag = 1
                self.file_sock.close()
                QMessageBox.information(self, 'information', '文件发送成功')
            elif self.flag == 10:
                self.file_sock.flush()
                self.index += 1
                if self.index < len(self.name_list):
                    self.folder_file_header()
                else:
                    self.index = 0
                    self.flag = 111 # 结束
                    self.file_header_slot()
            elif self.flag == 110:
                if self.null_flag == 1:
                    self.null_flag = 0
                    self.index = 0
                    self.flag = 111 # 结束
                    self.file_header_slot()
                else:
                    self.folder_file_header()
            elif self.flag == 111:
                self.send_folder_btn.setEnabled(False)
                self.shut_flag = 1
                self.file_sock.close()
                QMessageBox.information(self, 'information', '文件夹发送成功')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Warning', '确认退出？', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            self.shut_flag = 1
        else:
            event.ignore()

class File_download(QDialog):
    def __init__(self, ip, port):
        super(File_download, self).__init__()
        self.ip = ip
        self.port = port
        self.setWindowTitle("下载文件")
        self.setWindowIcon(QIcon(':/chat-download-line.png'))
        self.resize(1280, 720)
        self.setFixedSize(self.width(), self.height())
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(":/background5.jpeg")))
        self.setPalette(window_pale)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.label = QLabel("请选择需要下载的文件", self)
        self.label_down = QLabel('传输进度条:', self)
        self.label.setFont(QFont("宋体",12,QFont.Bold))
        self.label.setStyleSheet("color:red;")
        self.label.setGeometry(100,160,300,30)
        self.label_down.setFont(QFont("宋体",12,QFont.Bold))
        self.label_down.setStyleSheet("color:red;")
        self.label_down.setGeometry(100,480,110,30)
        self.cb = QComboBox(self)
        self.cb.setFont(QFont("宋体",12,QFont.Normal))
        self.cb.setGeometry(400,200,480,80)
        self.progress_bar = QProgressBar(self)
        self.button = QPushButton("下载", self)
        self.button.setEnabled(True)
        self.button.setIcon(QIcon(":/download-cloud-2-line.png"))
        self.button.setFont(QFont("宋体",10,QFont.Normal))
        self.button.setGeometry(930,360,100,40)
        self.button.setLayoutDirection(Qt.LeftToRight)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setGeometry(210,520,840,30)

        self.shut_flag = 0
        self.sock = QTcpSocket(self)
        self.connect_tcp()
        self.sock.readyRead.connect(self.read_data_slot)

        self.cb.currentIndexChanged.connect(self.select_slot)
        self.button.clicked.connect(self.button_slot)

    def connect_tcp(self):
        self.sock.connectToHost(self.ip, self.port + 200)
        self.sock.disconnected.connect(lambda: self.disconnected_slot(self.sock))
    
    def disconnected_slot(self, sock):
        sock.close()
        self.download_transfer_sock.close()
        if self.shut_flag == 0:     #停止传输
            QMessageBox.information(self, 'information', '服务器异常关闭')
            self.progress_bar.setValue(0)
                  
    def read_data_slot(self):
        while self.sock.bytesAvailable():
            datagram = self.sock.read(self.sock.bytesAvailable())
            message = datagram.decode()
            self.message1 = message.split("/")
            for item in self.message1:
                self.cb.addItem(item)
    
    def select_slot(self):
        self.selction = self.cb.currentText()
        self.index = self.cb.currentIndex()
        self.shut_flag = 0
        # self.sock.write(index)

    def button_slot(self):
        reply = QMessageBox.question(self, '下载确认', '确认下载文件：'+self.selction+"吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_path = QFileDialog.getExistingDirectory(self, '选择保存路径', os.getcwd())
            if len(self.save_path) == 0:
                 QMessageBox.critical(self, 'Wrong', '保存路径选择失败，请重新选择！')
            else:
                self.download_transfer_sock = QTcpSocket(self)
                self.download_transfer_sock.abort()
                self.download_transfer_sock.connectToHost(self.ip, self.port + 300)
                self.download_transfer_sock.readyRead.connect(self.read_file_slot)
                self.totalBytesToReceive = 0  # 要接收的数据的总大小
                self.bytesReceived = 0  # 已接收的数据大小
                self.fileNameSize = 0  # 文件名长度
                self.flag = 000   #区分是否为文件夹
                self.counter = 0
                self.sock.write(str(self.index).encode())
                self.button.setEnabled(False)
            
        else:
            QMessageBox.information(self, '取消下载', '请重新选择！')
            self.button.setEnabled(True)

    def read_file_slot(self):
        
        dataStream = QDataStream(self.download_transfer_sock)
        while self.download_transfer_sock.bytesAvailable():
            
        # 开始接收总字节数、文件名长度、文件名
            if self.bytesReceived <= 3:  # 接收到的数据小于sizeof(QInt64)*3，是刚开接收数据
                if self.download_transfer_sock.bytesAvailable() >= 3 and self.fileNameSize == 0:
                    self.totalBytesToReceive = dataStream.readInt64()
                    self.fileNameSize = dataStream.readInt64()
                    self.flag = dataStream.readInt64()
                    self.bytesReceived += 3
                    self.progress_bar.setValue(0)
                    if self.flag == 111:        #文件夹结束标记
                        self.shut_flag = 1
                        QMessageBox.information(self, 'information', '文件夹接收成功')
                        self.button.setEnabled(True)
                        self.sock.close()
                        self.download_transfer_sock.close()
                if self.download_transfer_sock.bytesAvailable() >= self.fileNameSize and self.fileNameSize != 0:
                    fileName = dataStream.readQString()
                    
                    self.bytesReceived += self.fileNameSize
                    if self.counter == 0:
                        self.dirpath = self.getUnrepeatSaveFilePath(self.save_path, fileName)
                        self.filePath = self.dirpath
                    else:
                        # 接收本地已有的同名文件时自动改名为不重复的文件路径
                        self.filePath = self.dirpath + fileName
                        
                    self.counter = 1
                    if int(self.flag/100) == 0:
                        self.toFile = QFile(self.filePath)
                        if not self.toFile.open(QFile.OpenModeFlag.WriteOnly):
                            QMessageBox.critical(self, 'Wrong', '无法打开文件')
                            return
                    elif int(self.flag/100) == 1:
                        os.mkdir(self.filePath)  
                else:
                    return
                        
            # 开始接收文件二进制数据流
            if self.bytesReceived < self.totalBytesToReceive and int(self.flag/100) == 0:  # 已接收的数据小于总数据，写入文件
                self.progress_bar.setValue(0)
                received = self.bytesReceived
                self.bytesReceived += min(self.totalBytesToReceive-self.bytesReceived, self.download_transfer_sock.bytesAvailable())
                bytes_obj = self.download_transfer_sock.read(min(self.totalBytesToReceive-received, self.download_transfer_sock.bytesAvailable()))
                qbyte = QByteArray(bytes_obj)
                self.toFile.write(qbyte)
                self.progress_bar.setValue(int(self.bytesReceived * 100 / self.totalBytesToReceive))

            # 接收完毕
            if self.bytesReceived == self.totalBytesToReceive:
                if self.flag == 10:
                    self.toFile.close()
                elif self.flag == 000:
                    self.toFile.close()
                    self.shut_flag = 1
                    self.download_transfer_sock.close()
                    self.sock.close()
                    QMessageBox.information(self, 'information', '文件接收成功')
                    self.button.setEnabled(True)
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

    # 关闭窗口时弹出确认消息
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Warning', '确认退出？', QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.shut_flag = 1
            event.accept()
        else:
            event.ignore()
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Client_Enter()
    demo.show()
    sys.exit(app.exec_())