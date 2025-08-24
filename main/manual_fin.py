from PyQt6.QtWidgets import QWidget, QPushButton, QSpacerItem, QSizePolicy, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont, QPixmap, QPalette, QBrush, QPainter

from PyQt6.QtCore import Qt, QMargins, QPointF
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument


class PDFView(QPdfView):
    def __init__(self, parent_viewer):
        super().__init__(parent_viewer)
        self.parent_viewer = parent_viewer
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
        self.setWindowTitle('Судный день - Правила игры')
        self.showFullScreen()

        self.parent = main

        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap('../source/design/manual_back.png')))
        self.setPalette(palette)

        font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 50)

        layout = QVBoxLayout(self)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        pdf_layout = QHBoxLayout()
        pdf_layout.addItem(QSpacerItem(180, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.prev_button = QPushButton()
        self.prev_button.setFixedSize(96, 96)
        self.white_arrow_back_icon = QPixmap('../source/design/arrow_back_white.png')
        self.gray_arrow_back_icon = QPixmap('../source/design/arrow_back_gray.png')
        self.black_arrow_back_icon = QPixmap('../source/design/arrow_back_black.png')
        self.prev_button.keyPressEvent = self.keyPressEvent
        self.prev_button.paintEvent = self.prev_button_icon_handler
        self.prev_button.clicked.connect(self.show_previous_page)
        pdf_layout.addWidget(self.prev_button, Qt.AlignmentFlag.AlignLeft)
        pdf_layout.addStretch(0)

        self.pdf_document = QPdfDocument(self)
        self.pdf_document.load('../source/manual.pdf')

        self.pdf_view = PDFView(self)
        self.pdf_view.setFixedSize(629, 920)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setDocumentMargins(QMargins(0, 0, 0, 0))
        self.pdf_view.setZoomFactor(1.285)
        self.pdf_view.setPageSpacing(0)

        self.navigator = self.pdf_view.pageNavigator()

        pdf_layout.addWidget(self.pdf_view)
        pdf_layout.addStretch(0)

        self.next_button = QPushButton()
        self.next_button.setFixedSize(96, 96)
        self.white_arrow_next_icon = QPixmap('../source/design/arrow_next_white.png')
        self.gray_arrow_next_icon = QPixmap('../source/design/arrow_next_gray.png')
        self.black_arrow_next_icon = QPixmap('../source/design/arrow_next_black.png')
        self.next_button.keyPressEvent = self.keyPressEvent
        self.next_button.paintEvent = self.next_button_icon_handler
        self.next_button.clicked.connect(self.show_next_page)
        pdf_layout.addWidget(self.next_button, Qt.AlignmentFlag.AlignRight)
        pdf_layout.addItem(QSpacerItem(180, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        layout.addLayout(pdf_layout)

        back_layout = QHBoxLayout()
        back_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.back_button = QPushButton('На главную')
        self.back_button.setFixedSize(220, 50)
        self.back_button.setFont(custom_font)
        self.back_button.clicked.connect(self.exit)
        self.back_button.setStyleSheet('QPushButton {background-color: transparent; color: white;}'
                                       'QPushButton:hover {color: gray;}'
                                       'QPushButton:pressed {color: black;}')
        back_layout.addWidget(self.back_button, Qt.AlignmentFlag.AlignLeft)
        back_layout.addStretch(0)

        layout.addLayout(back_layout)
        layout.addStretch(0)

    def prev_button_icon_handler(self, event):
        painter = QPainter(self.prev_button)
        icon = (self.black_arrow_back_icon if self.prev_button.isDown() else
                self.gray_arrow_back_icon if self.prev_button.underMouse() else self.white_arrow_back_icon)
        painter.drawPixmap(self.prev_button.rect(), icon)
        painter.end()

    def next_button_icon_handler(self, event):
        painter = QPainter(self.next_button)
        icon = (self.black_arrow_next_icon if self.next_button.isDown() else
                self.gray_arrow_next_icon if self.next_button.underMouse() else self.white_arrow_next_icon)
        painter.drawPixmap(self.next_button.rect(), icon)
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.exit()
        elif event.key() == Qt.Key.Key_Left:
            self.show_previous_page()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next_page()
        else:
            super().keyPressEvent(event)

    def show_previous_page(self):
        if self.navigator.currentPage() > 0:
            self.navigator.jump(self.navigator.currentPage() - 1, QPointF(0.1, 0.1))
        if self.navigator.currentPage() == 0:
            self.pdf_view.setFixedSize(629, 920)
        else:
            self.pdf_view.setFixedSize(1256, 920)

    def show_next_page(self):
        if self.navigator.currentPage() < self.pdf_document.pageCount() - 1:
            self.navigator.jump(self.navigator.currentPage() + 1, QPointF(0.1, 0.1))
        if self.navigator.currentPage() == 12 or self.navigator.currentPage() == 0:
            self.pdf_view.setFixedSize(629, 920)
        else:
            self.pdf_view.setFixedSize(1256, 920)

    def exit(self):
        self.parent.show()
        self.parent.on_reopen()
        self.close()
