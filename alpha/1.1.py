from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox
from PyQt6.QtCore import Qt, QPropertyAnimation
from connect import *
from lobby import *
from manual import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Полноэкранное окно с кнопками')
        # self.setWindowState(Qt.WindowState.WindowMaximized)

        layout = QHBoxLayout()
        layout.addStretch(0)

        button_layout = QVBoxLayout()
        button_layout.addStretch(2)

        button1_layout = QHBoxLayout()

        self.connect_button = QPushButton('Подключится')
        self.connect_button.setFixedWidth(220)
        self.connect_button.clicked.connect(self.connect_b_handler)
        button1_layout.addWidget(self.connect_button)

        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(4)
        self.spin_box.setMaximum(8)
        self.spin_box.setValue(4)
        self.spin_box.setSingleStep(1)
        button1_layout.addWidget(self.spin_box)

        button_layout.addLayout(button1_layout)

        connect_layout = QHBoxLayout()
        connect_layout.addStretch(0)

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

        self.manual_button = QPushButton('Правила игры')
        self.manual_button.clicked.connect(self.open_rules)
        button_layout.addWidget(self.manual_button)

        self.quit_button = QPushButton('Выйти')
        self.quit_button.clicked.connect(self.exit)
        button_layout.addWidget(self.quit_button)
        button_layout.addStretch(3)

        layout.addLayout(button_layout)
        layout.addStretch(0)

        self.setLayout(layout)

        self.manual_window = None
        self.game_window = None
        self.expanded = False

    def connect_b_handler(self):
        if self.expanded:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_connect((300, 0)))

            self.anim_lobby((150, 0))
            timer.start(500)
            self.expanded = False
        else:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_lobby((0, 150)))

            self.anim_connect((0, 300))
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
        self.close()

    def exit(self):
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
