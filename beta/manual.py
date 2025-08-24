from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtGui import QMovie, QPixmap, QFont, QFontDatabase, QIcon
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtCore import QPointF, QMargins

from PyQt6.QtCore import Qt


class PDFView(QPdfView):
    def __init__(self, parent_viewer, parent=None):
        super().__init__(parent)
        self.parent_viewer = parent_viewer

        # Отключаем полосу прокрутки
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Без рамок
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.parent_viewer.show_previous_page()
        elif event.key() == Qt.Key.Key_Right:
            self.parent_viewer.show_next_page()
        else:
            super().keyPressEvent(event)


class PDFViewer(QWidget):
    def __init__(self, main):
        super().__init__()
        try:
            self.setWindowTitle('PDF Viewer with QPdfPageNavigator')
            # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setWindowState(Qt.WindowState.WindowMaximized)
            # self.showFullScreen()

            pdf_path = 'manual.pdf'
            self.parent = main

            print(self.width(), self.height())

            # Создаем QLabel для фона
            self.background_label = QLabel(self)
            self.background_label.setGeometry(0, 0, self.width(), self.height())
            self.background_label.setScaledContents(True)

            image_path = "front/back_helper.png"  # Путь к статичной картинке

            pixmap = QPixmap(image_path)
            self.background_label.setPixmap(pixmap)

            self.layout = QVBoxLayout()

            nav_layout = QHBoxLayout()

            font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            custom_font = QFont(font_family[0], 50)  # Указываем размер шрифта

            lbl1 = QLabel()
            lbl1.setMinimumHeight(140)

            self.back_button = QPushButton('На главную', self)
            self.back_button.clicked.connect(self.exit)
            self.back_button.setFont(custom_font)  # Применяем кастомный шрифт
            self.back_button.setFixedWidth(350)
            self.back_button.setFixedHeight(50)

            self.back_button.setStyleSheet("""
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
            self.back_button.move(40, 900)

            nav_layout.addWidget(lbl1)

            self.prev_button = QPushButton(self)
            self.prev_button.clicked.connect(self.show_previous_page)

            # Устанавливаем иконку
            self.white_arrow_back_icon = QIcon("front/white_arrow_back.png")
            self.black_arrow_back_icon = QIcon("front/black_arrow_back.png")
            self.prev_button.setIcon(self.white_arrow_back_icon)
            self.prev_button.setStyleSheet("""
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


            # Настраиваем размер иконки относительно текста
            self.prev_button.setIconSize(self.prev_button.sizeHint())
            self.prev_button.setIconSize(QSize(64, 64))  # Устанавливаем размер иконки 64x64 пикселя
            self.prev_button.setFixedWidth(400)
            self.prev_button.setFixedHeight(100)

            self.prev_button.move(130, 450)


            self.next_button = QPushButton(self)
            self.next_button.clicked.connect(self.show_next_page)

            self.white_arrow_icon = QIcon("front/white_arrow.png")
            self.black_arrow_icon = QIcon("front/black_arrow.png")
            self.next_button.setIcon(self.white_arrow_icon)

            # Устанавливаем иконку
            # self.next_button.setIcon(icon)
            self.next_button.setStyleSheet("""
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

            # Настраиваем размер иконки относительно текста
            self.next_button.setIconSize(self.next_button.sizeHint())
            self.next_button.setIconSize(QSize(64, 64))  # Устанавливаем размер иконки 64x64 пикселя
            self.next_button.setFixedWidth(400)
            self.next_button.setFixedHeight(100)

            self.next_button.move(1400, 450)

            # nav_layout.addWidget(self.next_button)

            self.layout.addLayout(nav_layout)

            self.pdf_document = QPdfDocument(self)
            self.pdf_document.load(pdf_path)

            self.pdf_view = PDFView(self)
            self.pdf_view.setDocument(self.pdf_document)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setDocumentMargins(QMargins(0, 5, 0, 0))
            self.pdf_view.setZoomFactor(1.03)
            self.pdf_view.setPageSpacing(0)

            self.navigator = self.pdf_view.pageNavigator()

            self.layout.addWidget(self.pdf_view)

            self.layout.setContentsMargins(708, 18, 708, 173)

            self.setLayout(self.layout)


            self.pdf_view.setFocus()
            self.update_view()

            self.next_button.pressed.connect(self.change_to_black_arrow)
            self.next_button.released.connect(self.change_to_white_arrow)

            self.prev_button.pressed.connect(self.change_to_black_back_arrow)
            self.prev_button.released.connect(self.change_to_white_back_arrow)
        except Exception as e:
            print(e, '|init')

    def change_to_black_back_arrow(self):
        """Меняем иконку на black_arrow.png"""
        self.prev_button.setIcon(self.black_arrow_back_icon)

    def change_to_white_back_arrow(self):
        """Возвращаем иконку на white_arrow.png"""
        self.prev_button.setIcon(self.white_arrow_back_icon)

    def change_to_black_arrow(self):
        """Меняем иконку на black_arrow.png"""
        self.next_button.setIcon(self.black_arrow_icon)

    def change_to_white_arrow(self):
        """Возвращаем иконку на white_arrow.png"""
        self.next_button.setIcon(self.white_arrow_icon)

    # def resizeEvent(self, event):
    #     # Обновляем размер QLabel при изменении размера окна
    #     self.background_label.setGeometry(0, 0, self.width(), self.height())
    #     super().resizeEvent(event)

    def keyPressEvent(self, event):
        print(1)
        if event.key() == Qt.Key.Key_Left:
            self.show_previous_page()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next_page()
        else:
            super().keyPressEvent(event)

    def show_previous_page(self):
        if self.navigator.currentPage() > 0:
            self.navigator.jump(self.navigator.currentPage() - 1, QPointF(0.1, 0.1))
            self.update_view()
        if self.navigator.currentPage() == 0:
            self.layout.setContentsMargins(708, 18, 708, 173)
        else:
            self.layout.setContentsMargins(457, 18, 457, 173)  # Отступы по краям

    def show_next_page(self):
        if self.navigator.currentPage() < self.pdf_document.pageCount() - 1:
            self.navigator.jump(self.navigator.currentPage() + 1, QPointF(0.1, 0.1))
            self.update_view()
        if self.navigator.currentPage() == 12 or self.navigator.currentPage() == 0:
            self.layout.setContentsMargins(708, 18, 708, 173)
        else:
            self.layout.setContentsMargins(457, 18, 457, 173)  # Отступы по краям

    def update_view(self):
        current_page = self.navigator.currentPage() + 1
        total_pages = self.pdf_document.pageCount()
        self.setWindowTitle(f'PDF Viewer - Page {current_page}/{total_pages}')

    def closeEvent(self, event):
        self.exit()

    def exit(self):
        self.parent.show()
        self.close()
