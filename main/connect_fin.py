from PyQt6.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QSpacerItem, QSizePolicy, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont, QRegularExpressionValidator, QPixmap, QPainter
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QRegularExpression

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_BROADCAST
from json import dumps, loads
from threading import Thread
from time import sleep

from game_fin import Game


class Server(QThread):
    setAddress = pyqtSignal(tuple)
    newConnection = pyqtSignal(tuple)
    newMessage = pyqtSignal(dict)
    broadcastEnd = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.host = None
        self.socket = None

        self.broadcast_flag = True
        self.connect_flag = True
        self.receive_flag = True

    def run(self):
        try:
            self.host = self.get_local_ip()
            self.socket = self.get_socket()
            broadcast_thread = Thread(target=self.broadcast_presence, daemon=True)
            broadcast_thread.start()

            connect_thread = Thread(target=self.start_connect, daemon=True)
            connect_thread.start()

            broadcast_thread.join()
        except Exception as e:
            print(e, '|run')

    @staticmethod
    def get_local_ip():
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception as e:
            ip = '127.0.0.1'
            print(f'Ошибка определения ip адреса: {e}')
        finally:
            s.close()
        return ip

    def get_socket(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((self.host, 0))
        self.setAddress.emit(server_socket.getsockname())
        return server_socket

    def broadcast_presence(self):
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        target_address = ('<broadcast>', 50000)
        try:
            while self.broadcast_flag:
                try:
                    print('gg')
                    message = dumps({'purpose': 'pairing', 'host': self.host, 'port': self.socket.getsockname()[1]})
                    udp_socket.sendto(message.encode(), target_address)
                except Exception as e:
                    print(f'Ошибка отправки широковещательного сообщения: {e}')
                sleep(5)
        finally:
            udp_socket.close()

    def finish_broadcast(self):
        self.broadcast_flag = False

    def start_connect(self):
        try:
            self.socket.listen(4)
            while self.connect_flag:
                conn, addr = self.socket.accept()
                self.newConnection.emit(addr)
                receive_thread = Thread(target=self.start_receive, args=(conn,))
                receive_thread.start()
        finally:
            self.socket.close()

    def end_connect(self):
        self.connect_flag = False

    def start_receive(self, conn):
        while self.receive_flag:
            if not self.receive_flag:
                break
            try:
                data = conn.recv(2048).decode()
                if not data:
                    break
                # print(data)
                message = loads(data)
                print([message], 'message')
                self.newMessage.emit(message)
            except Exception as e:
                print(f'Ошибка подключения: {e},22222222')
                break

    def finish_receive(self):
        self.receive_flag = False


class ConnectPlayers(QThread):
    sendConnections = pyqtSignal(list)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

        self.servers = set()

    def run(self):
        self.find_servers()
        self.connect()

    def find_servers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', 50000))
        udp_socket.settimeout(300)
        try:
            while len(self.servers) < 3:  # это число игроков число - 1
                data, addr = udp_socket.recvfrom(1024)
                message = loads(data.decode())
                server = (message['host'], message['port'])
                if server != (self.host, int(self.port)):
                    self.servers.add(server)
        except socket.timeout:
            print('Таймаут: поиск завершён')
        except Exception as e:
            print(f'Ошибка при получении данных: {e}')

    def connect(self):
        try:
            connections = []
            for peer in self.servers:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((peer[0], int(peer[1])))
                connections.append(sock)
            self.sendConnections.emit(connections)
        except Exception as e:
            print(f'Ошибка подключения: {e}')


class AutoConnect(QThread):
    setAddress = pyqtSignal(tuple)
    newConnection = pyqtSignal(tuple)
    broadcastEnd = pyqtSignal()
    newMessage = pyqtSignal(dict)
    sendConnections = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.host = None
        self.port = None

        self.server_thread = None
        self.connection_thread = None

    def run(self):
        self.connect_server()

    def connect_server(self):
        try:
            if not self.server_thread or not self.server_thread.isRunning():
                self.server_thread = Server()
                self.server_thread.setAddress.connect(self.set_addr)
                self.server_thread.newConnection.connect(self.send_new_connection)
                # self.server_thread.broadcastEnd.connect(self)
                self.server_thread.newMessage.connect(self.send_new_message)
                self.server_thread.start()
        except Exception as e:
            print(e, '| connect_server')

    def set_addr(self, addr):
        self.host = addr[0]
        self.port = addr[1]
        self.setAddress.emit(addr)
        self.connect_players()

    def send_new_connection(self, text):
        self.newConnection.emit(text)

    def broadcast_end(self):
        self.broadcastEnd.emit()

    def send_new_message(self, text):
        self.newMessage.emit(text)

    def finish_broadcast(self):
        self.server_thread.finish_broadcast()

    def stop_server(self):
        self.server_thread.finish_broadcast()
        self.server_thread.finish_receive()
        self.server_thread.end_connect()
        self.server_thread.quit()
        self.server_thread.wait()

    def connect_players(self):
        try:
            if not self.connection_thread or not self.connection_thread.isRunning():
                self.connection_thread = ConnectPlayers(self.host, self.port)
                self.connection_thread.sendConnections.connect(self.send_connections)
                self.connection_thread.start()
        except Exception as e:
            print(e, '| auto_server')

    def send_connections(self, ls):
        self.sendConnections.emit(ls)

    def finish_connect(self):
        self.connection_thread.quit()
        self.connection_thread.wait()


class ConnectWindow(QWidget):
    addPlayer = pyqtSignal(str)
    getReady = pyqtSignal(str)
    lobbyRestart = pyqtSignal()

    def __init__(self, main):
        super().__init__()
        try:
            self.setFixedWidth(270)

            self.parent = main

            self.addr = None
            self.connections = []
            self.ready_counter = 0
            self.players = {}
            # self.left = None
            # self.opposite = None
            # self.right = None
            # self.first = None

            self.auto_connect_thread = None
            self.auto_connect_flag = False
            self.game_window = None

            font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            custom_font = QFont(font_family[0], 15)

            layout = QVBoxLayout(self)

            top_layout = QHBoxLayout()

            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText('Ник')
            self.name_edit.setFont(custom_font)
            self.name_edit.setValidator(QRegularExpressionValidator(QRegularExpression(f'^.{{0, 15}}$')))
            self.name_edit.textChanged.connect(self.name_handler)
            self.name_edit.setStyleSheet('QLineEdit {background: transparent; border-top: 2px solid white;'
                                         'border-bottom: 2px solid white; color: white;}')
            top_layout.addWidget(self.name_edit)
            top_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

            self.block_button = QPushButton('0')  # 1
            self.block_button.setFixedSize(30, 30)
            self.block_button.setEnabled(False)
            self.white_unlock_icon = QPixmap('../source/design/unlock_white.png')
            self.gray_unlock_icon = QPixmap('../source/design/unlock_gray.png')
            self.black_unlock_icon = QPixmap('../source/design/unlock_black.png')
            self.white_lock_icon = QPixmap('../source/design/lock_white.png')
            self.gray_lock_icon = QPixmap('../source/design/lock_gray.png')
            self.black_lock_icon = QPixmap('../source/design/lock_black.png')
            self.block_button.paintEvent = self.block_icon_handler
            self.block_button.clicked.connect(self.block_handler)
            top_layout.addWidget(self.block_button)
            top_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

            self.connect_button = QPushButton('0')  # ⭮
            self.connect_button.setFixedSize(30, 30)
            self.connect_button.setEnabled(False)
            self.white_connect_icon = QPixmap('../source/design/connect_white.png')
            self.gray_connect_icon = QPixmap('../source/design/connect_gray.png')
            self.black_connect_icon = QPixmap('../source/design/connect_black.png')
            self.white_reconnect_icon = QPixmap('../source/design/reconnect_white.png')
            self.gray_reconnect_icon = QPixmap('../source/design/reconnect_gray.png')
            self.black_reconnect_icon = QPixmap('../source/design/reconnect_black.png')
            self.connect_button.paintEvent = self.connect_icon_handler
            self.connect_button.clicked.connect(self.connect_handler)
            top_layout.addWidget(self.connect_button)

            layout.addLayout(top_layout)

            self.output_text_edit = QTextEdit()
            self.output_text_edit.setReadOnly(True)
            self.output_text_edit.setFont(custom_font)
            self.output_text_edit.setStyleSheet('QTextEdit {background-color: rgba(0, 0, 0, 100); border: 3px solid white;'
                                                'border-radius: 5px; padding: 3px; color: white;}')
            layout.addWidget(self.output_text_edit)

            chat_line_layout = QHBoxLayout()

            self.input_line_edit = QLineEdit()
            self.input_line_edit.setFont(custom_font)
            self.input_line_edit.setStyleSheet('QLineEdit {background: transparent; border-top: 2px solid white;'
                                               'border-bottom: 2px solid white; color: white;}')
            chat_line_layout.addWidget(self.input_line_edit)

            self.send_button = QPushButton('')
            self.send_button.setFixedSize(30, 30)
            self.send_button.setEnabled(False)
            self.white_send_icon = QPixmap('../source/design/send_white.png')
            self.gray_send_icon = QPixmap('../source/design/send_gray.png')
            self.black_send_icon = QPixmap('../source/design/send_black.png')
            self.send_button.paintEvent = self.send_icon_handler
            self.send_button.clicked.connect(lambda: self.send_message())
            chat_line_layout.addWidget(self.send_button)

            layout.addLayout(chat_line_layout)

        except Exception as e:
            print(e, '|init connect')

    def name_handler(self):
        if len(self.name_edit.text()) > 2:
            self.block_button.setEnabled(True)
        else:
            self.block_button.setEnabled(False)

    def block_icon_handler(self, event):
        painter = QPainter(self.block_button)
        if self.block_button.text() == '0':
            icon = (self.black_unlock_icon if self.block_button.isDown() or not self.block_button.isEnabled() else
                    self.gray_unlock_icon if self.block_button.underMouse() else self.white_unlock_icon)
        else:
            icon = (self.black_lock_icon if self.block_button.isDown() else self.gray_lock_icon
                    if self.block_button.underMouse() else self.white_lock_icon)
        painter.drawPixmap(self.block_button.rect(), icon)
        painter.end()

    def block_handler(self):
        if self.block_button.text() == '0':
            self.block_button.setText('1')
            self.name_edit.setEnabled(False)
            self.connect_button.setEnabled(True)
        elif self.block_button.text() == '1':
            self.block_button.setText('0')
            self.name_edit.setEnabled(True)
            self.connect_button.setEnabled(False)

    def connect_icon_handler(self, event):
        painter = QPainter(self.connect_button)
        if self.connect_button.text() == '0':
            icon = (self.black_connect_icon if self.connect_button.isDown() or not self.connect_button.isEnabled() else
                    self.gray_connect_icon if self.connect_button.underMouse() else self.white_connect_icon)
        else:
            icon = (self.black_reconnect_icon if self.connect_button.isDown() else self.gray_reconnect_icon
                    if self.connect_button.underMouse() else self.white_reconnect_icon)
        painter.drawPixmap(self.connect_button.rect(), icon)
        painter.end()

    def connect_handler(self):
        if self.connect_button.text() == '0':
            self.connect_button.setText('1')

        self.auto_connect()

    def send_icon_handler(self, event):
        painter = QPainter(self.send_button)
        icon = (self.black_send_icon if self.send_button.isDown() or not self.send_button.isEnabled() else
                self.gray_send_icon if self.send_button.underMouse() else self.white_send_icon)
        painter.drawPixmap(self.send_button.rect(), icon)
        painter.end()

    def auto_connect(self):
        try:
            if not self.auto_connect_thread or not self.auto_connect_flag:
                print(1)
                self.addPlayer.emit(self.name_edit.text())
                self.send_button.setEnabled(False)
                self.auto_connect_thread = AutoConnect()
                self.auto_connect_thread.setAddress.connect(self.set_addr)
                self.auto_connect_thread.newConnection.connect(self.write_connection)
                # self.auto_connect_thread.broadcastEnd.connect(self.)
                self.auto_connect_thread.newMessage.connect(self.message_handler)
                self.auto_connect_thread.sendConnections.connect(self.set_connections)
                self.auto_connect_thread.start()
                self.auto_connect_flag = True
            else:
                self.auto_connect_flag = False
                self.restart_connection()
        except Exception as e:
            print(e, '| auto_connect ConnectWindow')

    def set_addr(self, addr):
        self.output_text_edit.append(f'<font color="#c3383c">Адрес {addr[0]}:{addr[1]}<font>')
        self.addr = addr

    def write_connection(self, text):
        self.output_text_edit.append(f"\nПодключился <font color='#c3383c'>{text[0]}:{text[1]}</font>")

    def message_handler(self, message):
        if message['purpose'] == 'connect':
            self.players[message['name']] = message['from']
            self.output_text_edit.append(f"\nПодключился <font color='orange'>{message['name']}</font>")
            self.addPlayer.emit(message['name'])
        elif message['purpose'] == 'chat':
            self.output_text_edit.append(f"\n<font color='orange'>{message['name']}:</font> {message['message']}")
        elif message['purpose'] == 'ready':
            self.ready_counter += 1
            self.getReady.emit(message['name'])
        elif message['purpose'] == 'deal_sync':
            # print('принял')
            self.game_window.message_handler(message)
        elif message['purpose'] == 'fin_deal':
            self.game_window.message_handler(message)
        elif message['purpose'] == 'next':
            self.game_window.message_handler(message)

    def set_connections(self, conn):
        # print(conn)
        self.connections = conn

        message = {'purpose': 'connect',
                   'message': '',
                   'from': f'{self.addr[0]}:{self.addr[1]}',
                   'name': self.name_edit.text()}

        self.send_message(message)

        broadcast_timer = QTimer(self)
        broadcast_timer.setSingleShot(True)
        broadcast_timer.timeout.connect(self.auto_connect_thread.finish_broadcast)
        broadcast_timer.start(30000)

        self.send_button.setEnabled(True)

    def send_ready(self):
        self.ready_counter += 1
        self.getReady.emit(self.name_edit.text())

        message = {'purpose': 'ready',
                   'message': '',
                   'from': f'{self.addr[0]}:{self.addr[1]}',
                   'name': self.name_edit.text()}

        self.send_message(message)

    def player_distribution(self, sequence):
        print(sequence, 'sequence')
        self.players[self.name_edit.text()] = f'{self.addr[0]}:{self.addr[1]}'
        index = sequence.index(self.name_edit.text())
        right = {sequence[(index + 3) % 4]: self.players[sequence[(index + 3) % 4]]}
        opposite = {sequence[(index + 2) % 4]: self.players[sequence[(index + 2) % 4]]}
        left = {sequence[(index + 1) % 4]: self.players[sequence[(index + 1) % 4]]}
        first = {sequence[0]: self.players[sequence[0]]}
        print(left, opposite, right, 'sequence|sequence')
        if self.ready_counter == 4:
            self.game_window = Game(self.parent, self.name_edit.text(), [self.addr, left, opposite, right, first])
            self.game_window.sendMessage.connect(self.send_message)
            self.game_window.show()
            self.parent.hide()
            self.game_window.start()

    def restart_connection(self):
        self.ready_counter = 0
        self.players = {}
        # self.left = None
        # self.opposite = None
        # self.right = None
        # self.first = None
        self.lobbyRestart.emit()
        self.auto_connect_thread.finish_connect()
        self.auto_connect_thread.stop_server()
        self.auto_connect_thread.quit()
        self.auto_connect_thread.wait()
        self.auto_connect()

    def send_message(self, message=None):
        try:
            if message is None:
                message = {'purpose': 'chat',
                           'message': self.input_line_edit.text(),
                           'from': f'{self.addr[0]}:{self.addr[1]}',
                           'name': self.name_edit.text()}

                if len(message['message']) > 0:
                    self.output_text_edit.append(f"\n<font color='orange'>{message['name']}:</font> {message['message']}")

            print(message, 11111111111111111111)
            for sock in self.connections:
                try:
                    sock.send(dumps(message).encode())
                except Exception as e:
                    print(f'Ошибка отправки: {e}')
                self.input_line_edit.clear()
        except Exception as e:
            print(e, '|send_message')
