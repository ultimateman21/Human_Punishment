import sys
import socket
import threading
import json
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QSize, QRegularExpression
from PyQt6.QtGui import QFontDatabase, QFont, QIcon, QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QLabel, QHBoxLayout

from game import *


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
            broadcast_thread = threading.Thread(target=self.broadcast_presence, daemon=True)
            broadcast_thread.start()

            connect_thread = threading.Thread(target=self.start_connect, daemon=True)
            connect_thread.start()

            broadcast_thread.join()
        except Exception as e:
            print(e, '|run')

    @staticmethod
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, 0))
        self.setAddress.emit(server_socket.getsockname())
        return server_socket

    def broadcast_presence(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        target_address = ('<broadcast>', 50000)
        try:
            while self.broadcast_flag:
                try:
                    message = json.dumps({'purpose': 'pairing', 'host': self.host, 'port': self.socket.getsockname()[1]})
                    udp_socket.sendto(message.encode(), target_address)
                except Exception as e:
                    print(f'Ошибка отправки широковещательного сообщения: {e}')
                time.sleep(5)
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
                receive_thread = threading.Thread(target=self.start_receive, args=(conn,))
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
                message = json.loads(data)
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
                message = json.loads(data.decode())
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
        self.setWindowTitle('Чат-сервер')

        font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 15)  # Указываем размер шрифта
        custom_font1 = QFont(font_family[0], 15)  # Указываем размер шрифта

        self.auto_connect_thread = None
        self.auto_connect_flag = False
        self.addr = None
        self.connections = []
        self.ready_counter = 0
        self.players = {}
        self.left = None
        self.opposite = None
        self.right = None
        self.first = None

        self.game_window = None

        self.parent = main

        layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Ник')
        self.name_edit.setFixedWidth(150)
        self.name_edit.textChanged.connect(self.name_change)
        self.name_edit.setFont(custom_font1)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;  /* Убирает фон */
                border-left: none;         /* Убирает левую рамку */
                border-right: none;        /* Убирает правую рамку */
                border-top: 2px solid white;  /* Белая рамка сверху */
                border-bottom: 2px solid white; /* Белая рамка снизу */
                padding-left: 10px;        /* Отступ слева */
                padding-right: 10px;       /* Отступ справа */
                color: white;              /* Цвет текста */
            }
        """)
        regex = QRegularExpression(f"^.{{0, 8}}$")
        validator = QRegularExpressionValidator(regex)
        self.name_edit.setValidator(validator)
        top_layout.addWidget(self.name_edit)

        l1 = QLabel()

        self.name_block_button = QPushButton('0')  # 1
        self.name_block_button.setEnabled(False)
        self.name_block_button.clicked.connect(self.block_handler)
        self.unlock_icon = QIcon("front/unlock.png")
        self.lock_icon = QIcon("front/lock.png")
        self.name_block_button.setIcon(self.unlock_icon)
        self.name_block_button.setStyleSheet("""
                                            QPushButton {
                                                text-align: right; /* Для иконки справа от текста */
                                                background-color: transparent; /* Убирает фон */
                                                border: none; /* Убирает границы */
                                                color: transparent; /* Цвет текста */
                                            }
                                            QPushButton:hover {
                                                color: transparent; /* Цвет текста при наведении остается черным */
                                            }
                                        """)
        self.name_block_button.setIconSize(QSize(30, 30))
        top_layout.addWidget(l1)
        top_layout.addWidget(self.name_block_button)

        self.connect_button = QPushButton('1')  # ⭮
        self.connect_button.setEnabled(False)
        self.connect_icon = QIcon("front/connect.png")
        self.reconnect_icon = QIcon("front/reconnect.png")
        self.connect_button.clicked.connect(self.connect_handler)
        self.connect_button.setIcon(self.connect_icon)
        self.connect_button.setStyleSheet("""
                                            QPushButton {
                                                text-align: right; /* Для иконки справа от текста */
                                                background-color: transparent; /* Убирает фон */
                                                border: none; /* Убирает границы */
                                                color: transparent; /* Цвет текста */
                                            }
                                            QPushButton:hover {
                                                color: transparent; /* Цвет текста при наведении остается черным */
                                            }
                                        """)
        self.connect_button.setIconSize(QSize(30, 30))
        top_layout.addWidget(self.connect_button)
        layout.addLayout(top_layout)

        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: rgba(0, 0, 0, 100); /* Белый фон с прозрачностью */
                        border: 3px solid white; /* Белая граница толщиной 3 пикселя */
                        border-radius: 5px; /* Закругленные углы (по желанию) */
                        padding: 3px; /* Отступы внутри */
                        color: white; /* Черный цвет текста */
                    }
                """)
        # self.output_text_edit.append('<font color="orange">DenkiGO:</font> Привет!, как дела?')
        # self.output_text_edit.append('<font color="orange">XXX_b0d9a_XXX:</font> Хай! Норм')
        self.output_text_edit.setFont(custom_font)  # Применяем кастомный шрифт
        layout.addWidget(self.output_text_edit)

        chat_line_layout = QHBoxLayout()

        self.input_line_edit = QLineEdit()
        self.input_line_edit.setStyleSheet("""
                    QLineEdit {
                        background: transparent;  /* Убирает фон */
                        border-left: none;         /* Убирает левую рамку */
                        border-right: none;        /* Убирает правую рамку */
                        border-top: 2px solid white;  /* Белая рамка сверху */
                        border-bottom: 2px solid white; /* Белая рамка снизу */
                        padding-left: 10px;        /* Отступ слева */
                        padding-right: 10px;       /* Отступ справа */
                        color: white;              /* Цвет текста */
                    }
                """)
        self.input_line_edit.setFont(custom_font1)
        chat_line_layout.addWidget(self.input_line_edit)

        self.send_button = QPushButton('')
        self.white_arrow_back_icon = QIcon("front/send_white.png")
        self.black_arrow_back_icon = QIcon("front/send_black.png")
        self.send_button.setIcon(self.white_arrow_back_icon)
        self.send_button.setStyleSheet("""
                                    QPushButton {
                                        background-color: transparent; /* Убирает фон */
                                        border: none; /* Убирает границы */
                                        color: white; /* Цвет текста */
                                    }
                                    QPushButton:hover {
                                        color: white; /* Цвет текста при наведении остается черным */
                                    }
                                    QPushButton:pressed {
                                        color: black; /* Цвет текста при нажатии остается черным */
                                    }
                                """)
        self.send_button.setEnabled(False)
        self.send_button.setIconSize(QSize(30, 30))
        self.send_button.clicked.connect(lambda: self.send_message())

        self.send_button.pressed.connect(self.change_to_black_back_arrow)
        self.send_button.released.connect(self.change_to_white_back_arrow)
        chat_line_layout.addWidget(self.send_button)

        layout.addLayout(chat_line_layout)

        self.setLayout(layout)

    def change_to_black_back_arrow(self):
        """Меняем иконку на black_arrow.png"""
        self.send_button.setIcon(self.black_arrow_back_icon)

    def change_to_white_back_arrow(self):
        """Возвращаем иконку на white_arrow.png"""
        self.send_button.setIcon(self.white_arrow_back_icon)

    def name_change(self):
        if len(self.name_edit.text()) > 2:
            self.name_block_button.setEnabled(True)
        else:
            self.name_block_button.setEnabled(False)

    def block_handler(self):
        if self.name_block_button.text() == '0':
            self.name_block_button.setText('1')
            self.name_block_button.setIcon(self.lock_icon)
            self.name_edit.setEnabled(False)
            self.connect_button.setEnabled(True)
        elif self.name_block_button.text() == '1':
            self.name_block_button.setText('0')
            self.name_block_button.setIcon(self.unlock_icon)
            self.name_edit.setEnabled(True)
            self.connect_button.setEnabled(False)

    def connect_handler(self):
        if self.connect_button.text() == '1':
            self.connect_button.setText('0')

        self.auto_connect()

    def auto_connect(self):
        try:
            if not self.auto_connect_thread or not self.auto_connect_flag:
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
        self.players[self.name_edit.text()] = f'{self.addr[0]}:{self.addr[1]}'
        index = sequence.index(self.name_edit.text())
        self.right = {sequence[(index + 3) % 4]: self.players[sequence[(index + 3) % 4]]}
        self.opposite = {sequence[(index + 2) % 4]: self.players[sequence[(index + 2) % 4]]}
        self.left = {sequence[(index + 1) % 4]: self.players[sequence[(index + 1) % 4]]}
        self.first = {sequence[0]: self.players[sequence[0]]}
        if self.ready_counter == 4:
            self.game_window = Game(self.parent, self.name_edit.text(), [self.addr, self.right, self.opposite, self.left, self.first])
            self.game_window.sendMessage.connect(self.send_message)
            self.game_window.show()
            self.parent.hide()
            self.game_window.start()

    # def message_from_game(self, message):
    #     print(message, 444444)

    def restart_connection(self):
        self.ready_counter = 0
        self.players = {}
        self.left = None
        self.opposite = None
        self.right = None
        self.first = None
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
                    sock.send(json.dumps(message).encode())
                except Exception as e:
                    print(f'Ошибка отправки: {e}')
                self.input_line_edit.clear()
        except Exception as e:
            print(e, '|send_message')
