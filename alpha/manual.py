from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtCore import QPointF, QMargins


class PDFView(QPdfView):
    def __init__(self, parent_viewer, parent=None):
        super().__init__(parent)
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
        self.setWindowTitle('PDF Viewer with QPdfPageNavigator')
        self.setWindowState(Qt.WindowState.WindowMaximized)

        self.parent = main

        layout = QVBoxLayout()

        nav_layout = QHBoxLayout()

        self.back_button = QPushButton('На главную')
        self.back_button.setFixedWidth(100)
        self.back_button.clicked.connect(self.exit)
        nav_layout.addWidget(self.back_button)

        self.prev_button = QPushButton('Previous')
        self.prev_button.clicked.connect(self.show_previous_page)
        nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.show_next_page)
        nav_layout.addWidget(self.next_button)

        layout.addLayout(nav_layout)

        self.pdf_document = QPdfDocument(self)
        self.pdf_document.load('../source/manual.pdf')

        self.pdf_view = PDFView(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setDocumentMargins(QMargins(0, 5, 0, 0))
        self.pdf_view.setZoomFactor(1.03)
        self.pdf_view.setPageSpacing(0)

        self.navigator = self.pdf_view.pageNavigator()

        layout.addWidget(self.pdf_view)

        self.setLayout(layout)
        self.pdf_view.setFocus()
        self.update_view()

    def keyPressEvent(self, event):
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

    def show_next_page(self):
        if self.navigator.currentPage() < self.pdf_document.pageCount() - 1:
            self.navigator.jump(self.navigator.currentPage() + 1, QPointF(0.1, 0.1))
            self.update_view()

    def update_view(self):
        current_page = self.navigator.currentPage() + 1
        total_pages = self.pdf_document.pageCount()
        self.setWindowTitle(f'PDF Viewer - Page {current_page}/{total_pages}')

    def closeEvent(self, event):
        self.exit()

    def exit(self):
        self.parent.show()
        self.close()
