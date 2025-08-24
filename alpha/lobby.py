from PyQt6.QtWidgets import QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class Lobby(QWidget):
    pressReady = pyqtSignal()
    sequenceFull = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('')
        self.setGeometry(100, 100, 500, 400)

        self.sequence =[]

        layout = QVBoxLayout()

        lobby_layout = QVBoxLayout()
        player_layout = QGridLayout()

        self.player_1 = QLabel('')
        player_layout.addWidget(self.player_1, 0, 0)

        self.player_1_state = QLabel('0')
        player_layout.addWidget(self.player_1_state, 0, 1)

        self.player_2 = QLabel('')
        player_layout.addWidget(self.player_2, 1, 0)

        self.player_2_state = QLabel('0')
        player_layout.addWidget(self.player_2_state, 1, 1)

        self.player_3 = QLabel('')
        player_layout.addWidget(self.player_3, 2, 0)

        self.player_3_state = QLabel('0')
        player_layout.addWidget(self.player_3_state, 2, 1)

        self.player_4 = QLabel('')
        player_layout.addWidget(self.player_4, 3, 0)

        self.player_4_state = QLabel('0')
        player_layout.addWidget(self.player_4_state, 3, 1)

        self.players = [(self.player_1, self.player_1_state),
                        (self.player_2, self.player_2_state),
                        (self.player_3, self.player_3_state),
                        (self.player_4, self.player_4_state)]

        lobby_layout.addLayout(player_layout)
        lobby_layout.addStretch(0)

        layout.addLayout(lobby_layout)

        self.ready_button = QPushButton('Готов')
        self.ready_button.setEnabled(False)
        self.ready_button.clicked.connect(self.ready_press)
        layout.addWidget(self.ready_button)

        self.setLayout(layout)

    def set_player(self, name):
        for player in self.players:
            if player[0].text() == '':
                player[0].setText(name)
                if player[0] is self.player_1:
                    self.ready_button.setEnabled(True)
                break

    def set_state(self, name):
        for player in self.players:
            if player[0].text() == name:
                player[1].setText('1')
                self.sequence.append(name)
                if len(self.sequence) == 4:
                    self.sequenceFull.emit(self.sequence)
                break

    def ready_press(self):
        self.ready_button.setEnabled(False)
        self.pressReady.emit()

    def restart(self):
        for i in self.players:
            i[0].setText('')
            i[1].setText('0')
        self.ready_button.setEnabled(False)
