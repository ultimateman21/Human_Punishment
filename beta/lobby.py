from PyQt6.QtGui import QFontDatabase, QFont, QIcon
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

        font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 24)  # Указываем размер шрифта

        custom_font1 = QFont(font_family[0], 16)  # Указываем размер шрифта

        layout = QVBoxLayout()
        l1 = QLabel()
        l1.setFont(custom_font1)

        player_layout = QGridLayout()

        player_layout.addWidget(l1, 0, 0)

        lobby_layout = QVBoxLayout()

        self.red_icon = QIcon("front/red_icon.png")
        self.green_icon = QIcon("front/green_icon.png")

        self.player_1 = QLabel('')
        self.player_1.setFont(custom_font)
        self.player_1.setStyleSheet("QLabel { color: white; }")
        self.player_1.setFixedWidth(170)
        player_layout.addWidget(self.player_1, 1, 0)

        self.player_1_state = QLabel('')
        player_layout.addWidget(self.player_1_state, 1, 1)

        self.player_2 = QLabel('')
        self.player_2.setFont(custom_font)
        self.player_2.setStyleSheet("QLabel { color: white; }")
        player_layout.addWidget(self.player_2, 2, 0)

        self.player_2_state = QLabel('')
        player_layout.addWidget(self.player_2_state, 2, 1)

        self.player_3 = QLabel('')
        self.player_3.setFont(custom_font)
        self.player_3.setStyleSheet("QLabel { color: white; }")
        player_layout.addWidget(self.player_3, 3, 0)

        self.player_3_state = QLabel('')
        player_layout.addWidget(self.player_3_state, 3, 1)

        self.player_4 = QLabel('')
        self.player_4.setFont(custom_font)
        self.player_4.setStyleSheet("QLabel { color: white; }")
        player_layout.addWidget(self.player_4, 4, 0)

        self.player_4_state = QLabel('')
        player_layout.addWidget(self.player_4_state, 4, 1)

        self.players = [(self.player_1, self.player_1_state),
                        (self.player_2, self.player_2_state),
                        (self.player_3, self.player_3_state),
                        (self.player_4, self.player_4_state)]

        lobby_layout.addLayout(player_layout)
        lobby_layout.addStretch(0)

        layout.addLayout(lobby_layout)

        self.ready_button = QPushButton('ГОТОВ')
        self.ready_button.setFixedWidth(350)
        self.ready_button.setFont(custom_font)  # Применяем кастомный шрифт
        self.ready_button.setStyleSheet("""
                    QPushButton {
                        text-align: left; /* Выравнивание текста влево */
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
            i[1].setText('0')
        self.ready_button.setEnabled(False)
