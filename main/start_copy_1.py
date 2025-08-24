from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QSpacerItem, QSizePolicy, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont, QMovie, QPalette, QBrush, QPixmap, QPainter
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation

from connect_fin import ConnectWindow
from manual_fin import PDFViewer
from lobby_fin import Lobby

from os.path import exists

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle('Судный день')
            self.showFullScreen()

            font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            custom_font = QFont(font_family[0], 50)

            gif_path = '../source/design/menu_back_gif.gif'
            image_path = '../source/design/menu_back_img.png'

            if exists(gif_path):  # Проверка наличия GIF
                self.movie = QMovie(gif_path)
                self.movie.start()
                gif_timer = QTimer(self)
                gif_timer.timeout.connect(self.update)
                gif_timer.start(1000 // self.movie.speed())  # Частота обновления GIF
            elif exists(image_path):  # Если GIF не найден, устанавливаем картинку
                palette = QPalette()
                palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap(image_path)))
                self.setPalette(palette)
            else:  # Если ни GIF, ни картинка не найдены, оставить фон пустым
                print('Фон недоступен')

            layout = QVBoxLayout(self)

            label = QLabel()
            label.setPixmap(QPixmap('../source/design/game_name.png'))
            layout.addWidget(label)

            layout.addItem(QSpacerItem(20, 100, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

            button_layout = QVBoxLayout()
            button_layout.setContentsMargins(20, 0, 0, 0)

            button_stile = ('QPushButton {text-align: left; background-color: transparent; color: white;}'
                            'QPushButton:hover {color: gray;}'
                            'QPushButton:pressed {color: black;}')

            self.connect_button = QPushButton('Подключится')
            self.connect_button.setFixedSize(250, 50)
            self.connect_button.setFont(custom_font)
            self.connect_button.setStyleSheet(button_stile)
            self.connect_button.clicked.connect(self.connect_b_handler)
            button_layout.addWidget(self.connect_button)

            connect_layout = QHBoxLayout()
            self.connect_wid = ConnectWindow(self)
            self.connect_wid.setMaximumHeight(0)
            self.connect_wid.setMinimumHeight(0)
            self.connect_wid_min = QPropertyAnimation(self.connect_wid, b"minimumHeight")
            self.connect_wid_max = QPropertyAnimation(self.connect_wid, b"maximumHeight")
            self.connect_wid_min.setDuration(300)
            self.connect_wid_max.setDuration(300)
            self.connect_wid.addPlayer.connect(self.add_player)
            self.connect_wid.getReady.connect(self.get_ready)
            self.connect_wid.lobbyRestart.connect(self.lobby_restart)
            connect_layout.addWidget(self.connect_wid)

            self.lobby_wid = Lobby()
            self.lobby_wid.setMaximumWidth(0)
            self.lobby_wid.setMinimumWidth(0)
            self.lobby_wid.setMaximumHeight(0)
            self.lobby_wid.setMinimumHeight(0)
            self.lobby_wid_min_w = QPropertyAnimation(self.lobby_wid, b"minimumWidth")
            self.lobby_wid_max_w = QPropertyAnimation(self.lobby_wid, b"maximumWidth")
            self.lobby_wid_min_h = QPropertyAnimation(self.lobby_wid, b"minimumHeight")
            self.lobby_wid_max_h = QPropertyAnimation(self.lobby_wid, b"maximumHeight")
            self.lobby_wid_min_w.setDuration(300)
            self.lobby_wid_max_w.setDuration(300)
            self.lobby_wid_min_h.setDuration(300)
            self.lobby_wid_max_h.setDuration(300)
            self.lobby_wid.pressReady.connect(self.send_ready)
            self.lobby_wid.sequenceFull.connect(self.player_sequence)
            connect_layout.addWidget(self.lobby_wid)
            connect_layout.addStretch(0)

            button_layout.addLayout(connect_layout)
            button_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

            self.manual_button = QPushButton('Правила игры')
            self.manual_button.setFixedSize(265, 70)
            self.manual_button.setFont(custom_font)
            self.manual_button.setStyleSheet(button_stile)
            self.manual_button.clicked.connect(self.open_rules)
            button_layout.addWidget(self.manual_button)
            button_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

            self.quit_button = QPushButton('Выйти')
            self.quit_button.setFixedSize(120, 55)
            self.quit_button.setFont(custom_font)
            self.quit_button.setStyleSheet(button_stile)
            self.quit_button.clicked.connect(self.exit)
            button_layout.addWidget(self.quit_button)

            layout.addLayout(button_layout)
            layout.addStretch(0)

            self.manual_window = None
            self.game_window = None
            self.expanded = False
        except Exception as e:
            print(e, '|init')

    def paintEvent(self, event):
        if hasattr(self, 'movie'):
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self.movie.currentPixmap())

    def connect_b_handler(self):
        if self.expanded:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_connect((300, 0)))
            self.anim_lobby((305, 0))
            timer.start(500)
            self.expanded = False
        else:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_lobby((0, 305)))
            self.anim_connect((0, 400))
            timer.start(500)
            self.expanded = True

    def anim_connect(self, param):
        self.connect_wid_min.setStartValue(param[0])
        self.connect_wid_min.setEndValue(param[1])
        self.connect_wid_max.setStartValue(param[0])
        self.connect_wid_max.setEndValue(param[1])

        self.lobby_wid_min_h.setStartValue(param[0])
        self.lobby_wid_min_h.setEndValue(param[1])
        self.lobby_wid_max_h.setStartValue(param[0])
        self.lobby_wid_max_h.setEndValue(param[1])

        self.connect_wid_min.start()
        self.connect_wid_max.start()
        self.lobby_wid_min_h.start()
        self.lobby_wid_max_h.start()

    def anim_lobby(self, param):
        self.lobby_wid_min_w.setStartValue(param[0])
        self.lobby_wid_max_w.setEndValue(param[1])
        self.lobby_wid_min_w.setStartValue(param[0])
        self.lobby_wid_max_w.setEndValue(param[1])

        self.lobby_wid_min_w.start()
        self.lobby_wid_max_w.start()

    def add_player(self, name):
        self.lobby_wid.set_player(name)

    def send_ready(self):
        self.connect_wid.send_ready()

    def get_ready(self, name):
        self.lobby_wid.set_state(name)

    def player_sequence(self, sequence):
        self.connect_wid.player_distribution(sequence)

    def lobby_restart(self):
        self.lobby_wid.restart()

    def open_rules(self):
        self.manual_window = PDFViewer(self)
        self.manual_window.show()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def on_reopen(self):
        self.resize(1920, 1080)

    def exit(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec())
