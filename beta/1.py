import os

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QParallelAnimationGroup
from connect import *
from lobby import *
from manual import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Полноэкранное окно с кнопками')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        # self.showFullScreen()

        # Создаем QLabel для фона
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.setScaledContents(True)

        font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 50)  # Указываем размер шрифта

        custom_font1 = QFont(font_family[0], 40)

        label = QLabel(self)
        pixmap = QPixmap("front/name_game.png")
        label.setPixmap(pixmap)
        label.setFixedHeight(250)
        label.setFixedWidth(1200)
        label.move(10, 10)

        # Попытка загрузить GIF
        gif_path = "front/main_menu_beck-001.gif"
        image_path = "front/mein_menu_beck_img.png"  # Путь к статичной картинке

        if os.path.exists(gif_path):  # Проверка наличия GIF
            self.movie = QMovie(gif_path)
            self.background_label.setMovie(self.movie)
            self.movie.start()
        elif os.path.exists(image_path):  # Если GIF не найден, устанавливаем картинку
            pixmap = QPixmap(image_path)
            self.background_label.setPixmap(pixmap)
        else:  # Если ни GIF, ни картинка не найдены, оставить фон пустым
            self.background_label.setText("Фон недоступен")
            self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Основной контейнер для layout
        self.layout_widget = QWidget(self)
        self.layout_widget.setGeometry(25, 290, 350, 300)  # Начальная позиция и размер

        layout = QHBoxLayout(self.layout_widget)
        # layout.addStretch(0)

        button_layout = QVBoxLayout()
        button_layout.addStretch(2)

        button1_layout = QHBoxLayout()

        self.connect_button = QPushButton('Подключится')
        self.connect_button.setFixedWidth(220)
        self.connect_button.clicked.connect(self.connect_b_handler)
        self.connect_button.setFont(custom_font)  # Применяем кастомный шрифт
        self.connect_button.setFixedWidth(267)
        self.connect_button.setFixedHeight(50)
        self.connect_button.setStyleSheet("""
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

        button_layout.addWidget(self.connect_button)

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
        self.manual_button.setFont(custom_font)  # Применяем кастомный шрифт
        self.manual_button.setStyleSheet("""
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
        button_layout.addWidget(self.manual_button)

        self.quit_button = QPushButton('Выйти')
        self.quit_button.clicked.connect(self.exit)
        self.quit_button.setFont(custom_font)  # Применяем кастомный шрифт
        self.quit_button.setStyleSheet("""
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
        button_layout.addWidget(self.quit_button)
        button_layout.addStretch(3)

        layout.addLayout(button_layout)
        layout.addStretch(0)

        # self.setLayout(layout)

        self.manual_window = None
        self.game_window = None
        self.expanded = False
        print(self.width(), self.height())

    def animate_layout_widget(self, start_rect, end_rect, timer):
        """Анимация перемещения layout_widget"""
        self.animation = QPropertyAnimation(self.layout_widget, b"geometry")
        self.animation.setDuration(timer)  # Длительность анимации в миллисекундах
        self.animation.setStartValue(start_rect)  # Начальная позиция и размер
        self.animation.setEndValue(end_rect)  # Конечная позиция и размер
        self.animation.start()

    def resizeEvent(self, event):
        if hasattr(self, 'background_label') and self.background_label is not None:
            self.background_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def connect_b_handler(self):
        if self.expanded:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_connect((400, 0)))

            self.anim_lobby((150, 0))
            timer.start(200)

            self.animate_layout_widget(QRect(25, 210, 450, 900), QRect(25, 290, 350, 300), 600)

            self.expanded = False
        else:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.anim_lobby((0, 150)))

            self.anim_connect((0, 400))

            self.animate_layout_widget(QRect(25, 290, 350, 300), QRect(25, 210, 450, 900), 300)

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
