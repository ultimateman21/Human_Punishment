from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout
from PyQt6.QtGui import QFontDatabase, QFont, QIcon
from PyQt6.QtCore import pyqtSignal


class Lobby(QWidget):
    pressReady = pyqtSignal()
    sequenceFull = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.sequence = []

        font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 24)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 47, 10, 7)

        player_panel = QWidget()
        player_panel.setStyleSheet('QWidget {background-color: rgba(0, 0, 0, 135); border-radius: 5px; border: 3px solid white;}')

        player_layout = QGridLayout(player_panel)

        self.red_icon = QIcon('../source/design/circle_red.png')
        self.green_icon = QIcon('../source/design/circle_green.png')

        self.players = []
        for row in range(4):
            state_label = QLabel()
            state_label.setFixedWidth(18)
            state_label.setStyleSheet('QLabel {background-color: transparent; color: white; border: none}')

            name_label = QLabel('')
            name_label.setFont(custom_font)
            name_label.setStyleSheet('QLabel {background-color: transparent; color: white; border: none}')

            player_layout.addWidget(state_label, row, 0)
            player_layout.addWidget(name_label, row, 1)

            self.players.append((name_label, state_label))

        player_layout.setRowStretch(4, 1)
        layout.addWidget(player_panel)

        self.ready_button = QPushButton('ГОТОВ')
        self.ready_button.setEnabled(False)
        self.ready_button.setFixedSize(305, 33)
        self.ready_button.setFont(custom_font)
        self.ready_button.clicked.connect(self.ready_press)
        self.ready_button.setStyleSheet('QPushButton {text-align: left; background-color: transparent; color: white;}'
                                        'QPushButton:hover {color: gray;}'
                                        'QPushButton:pressed {color: black;}'
                                        'QPushButton:disabled {color: black;}')
        layout.addWidget(self.ready_button)

    def set_player(self, name):
        for player in self.players:
            if player[0].text() == '':
                player[1].setPixmap(self.red_icon.pixmap(18, 18))
                player[0].setText(name)
                if player[0] is self.players[0][0]:
                    self.ready_button.setEnabled(True)
                break

    def set_state(self, name):
        for player in self.players:
            if player[0].text() == name:
                player[1].setPixmap(self.green_icon.pixmap(18, 18))
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
            i[1].setText('')
        self.ready_button.setEnabled(False)
