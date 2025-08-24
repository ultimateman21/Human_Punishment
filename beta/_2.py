import json
from PIL import Image
from PyQt6.QtGui import QPainter, QPixmap, QImage, QTransform, QFontDatabase, QFont, QColor, QPen, QBrush
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene, QApplication, QGraphicsPixmapItem, \
    QDialog, QLabel, QPushButton, \
    QHBoxLayout, QGraphicsDropShadowEffect, QGraphicsRectItem
from PyQt6.QtCore import Qt, QPointF, QVariantAnimation, pyqtSignal, QTimer
from random import sample
from copy import deepcopy


class Card(QGraphicsPixmapItem):
    def __init__(self, player, card_type, type_, pos, data, hided, order=None, parent=None):
        super().__init__(parent)
        self.player = player
        self.card_type = card_type
        self.type = type_
        self.pos = pos
        self.data = data
        self.order = order
        self.hided = hided

        self.offset = {'center': 0, 'self': 0, 'left': 90, 'opposite': 180, 'right': 270}
        self.action_previous = {'self': 'right', 'left': 'self', 'opposite': 'left', 'right': 'opposite'}

        if self.card_type in ['program', 'weapon', 'action']:
            self.width = 220
            self.height = 140
            if self.card_type == 'action':
                transform = QTransform()
                transform.translate(self.width / 2, self.height / 2)
                transform.rotate(self.offset[self.player])
                transform.translate(-self.width / 2, -self.height / 2)
                self.setTransform(transform)
        else:
            self.width = 140
            self.height = 220
            transform = QTransform()
            transform.translate(self.width / 2, self.height / 2)
            transform.rotate(90)
            transform.translate(-self.width / 2, -self.height / 2)
            self.setTransform(transform)

        self.front = self.data['front_path']
        self.back = self.data['back_path']
        self.description = self.data['description']

        self.front_img = self.load_and_scale_image(self.front, self.width, self.height)
        self.back_img = self.load_and_scale_image(self.back, self.width, self.height)

        self.setPixmap(self.back_img)  # Начальное состояние — рубашка карты

        self.move_animation = None
        self.to_default_animation = None

        self.is_open = False
        self.flip_animation = None

        self.is_rotate = False
        self.rotate_animation = None
        if self.type != 'action':
            self.setPos(QPointF(*self.pos['center'][self.type]))
        else:
            self.setPos(QPointF(*self.pos[self.player][self.type]))

    @staticmethod
    def load_and_scale_image(image_path, target_width, target_height):
        image = Image.open(image_path)
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        data = image.tobytes('raw', 'RGBA')
        return QPixmap.fromImage(QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888))

    def set_hided(self, flag):
        self.hided = flag

    def move_to(self, start_pos, end_pos, finish):
        self.setZValue(1)
        if end_pos is not None:
            self.move_animation = QVariantAnimation()
            self.move_animation.setDuration(1000)
            self.move_animation.setStartValue(QPointF(*start_pos))
            self.move_animation.setEndValue(QPointF(*end_pos))

            def on_value_changed(value):
                self.setPos(value)

            self.move_animation.valueChanged.connect(on_value_changed)
            self.move_animation.finished.connect(finish)
            self.move_animation.start()

    def move_to_default(self):
        try:
            if self.type != 'action':
                if self.order is None:
                    self.move_to(self.pos['center'][self.type], self.pos[self.player][self.type], self.rotate_to_default)
                else:
                    self.move_to(self.pos['center'][self.type], self.pos[self.player][self.type][self.order], self.rotate_to_default)
        except Exception as e:
            print(e, '|move')

    # def move_program_to_center(self):
    #     self.move_to(self.pos[self.player]['program'][self.order], self.pos['center']['program'])
    #
    # def move_program_to_slot(self, order):
    #     self.order = order
    #     self.move_to(self.pos['center']['program'], self.pos[self.player]['program'][self.order])
    #
    # def move_weapon_to_center(self):
    #     self.move_to(self.pos[self.player]['weapon'], self.pos['center'][self.type])
    #
    # def move_weapon_to_slot(self):
    #     self.move_to(self.pos['center'][self.type], self.pos[self.player]['weapon'])

    def move_action(self):
        self.move_to(self.pos[self.action_previous[self.player]]['action'], self.pos[self.player]['action'], self.rotate_action)

    def rotate_to(self, start_angle, end_angle):
        self.to_default_animation = QVariantAnimation()
        self.to_default_animation.setDuration(700)

        self.to_default_animation.setStartValue(start_angle)
        self.to_default_animation.setEndValue(end_angle)

        def on_value_changed(value):
            transform = QTransform()
            transform.translate(self.width / 2, self.height / 2)
            transform.rotate(value)
            transform.translate(-self.width / 2, -self.height / 2)
            self.setTransform(transform)

        def on_finished():
            transform = self.transform()
            transform.reset()
            transform.translate(self.width / 2, self.height / 2)
            transform.rotate(end_angle)
            transform.translate(-self.width / 2, -self.height / 2)
            self.setTransform(transform)
            self.setZValue(0)

        self.to_default_animation.valueChanged.connect(on_value_changed)
        self.to_default_animation.finished.connect(on_finished)
        self.to_default_animation.start()

    def rotate_to_default(self):
        self.rotate_to(90 if self.card_type not in ['program', 'weapon', 'action'] else 0,
                       self.offset[self.player] if self.card_type not in ['program', 'weapon', 'action'] else self.offset[self.player])

    def rotate_action(self):
        if self.player != 'self':
            self.rotate_to(self.offset[self.action_previous[self.player]], self.offset[self.player])
        else:
            self.rotate_to(self.offset[self.action_previous[self.player]], 360)

    def set_scale_x(self, value):
        transform = self.transform()
        transform.reset()
        transform.translate(self.width / 2, self.height / 2)
        transform.rotate(90 + self.offset[self.player] if self.is_rotate else 0 + self.offset[self.player])
        transform.scale(value, 1.0)
        transform.translate(-self.width / 2, -self.height / 2)
        self.setTransform(transform)

    def flip(self):
        self.flip_animation = QVariantAnimation()
        self.flip_animation.setDuration(500)
        self.flip_animation.setStartValue(1.0)
        self.flip_animation.setKeyValueAt(0.5, 0.0)
        self.flip_animation.setEndValue(1.0)

        def on_value_changed(value):
            self.set_scale_x(value)
            if value <= 0.1:
                self.setPixmap(self.front_img if not self.is_open else self.back_img)

        def on_finished():
            self.is_open = not self.is_open

        self.flip_animation.valueChanged.connect(on_value_changed)
        self.flip_animation.finished.connect(on_finished)
        self.flip_animation.start()

    def rotate_90(self):
        self.rotate_animation = QVariantAnimation()
        self.rotate_animation.setDuration(500)

        self.rotate_animation.setStartValue(90 if self.is_rotate else 0)
        self.rotate_animation.setEndValue(0 if self.is_rotate else 90)

        def on_value_changed(value):
            transform = QTransform()
            transform.translate(self.width / 2, self.height / 2)
            transform.rotate(value + self.offset[self.player])
            transform.translate(-self.width / 2, -self.height / 2)
            self.setTransform(transform)

        def on_finished():
            self.is_rotate = not self.is_rotate

        self.rotate_animation.valueChanged.connect(on_value_changed)
        self.rotate_animation.finished.connect(on_finished)
        self.rotate_animation.start()


class CardPreviewDialog(QDialog):
    actionButton = pyqtSignal(dict)
    goNext = pyqtSignal()

    def __init__(self, im_path, desc, type_, parent=None):
        super().__init__(parent)

        font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 50)  # Указываем размер шрифта
        custom_font1 = QFont(font_family[0], 20)  # Указываем размер шрифта

        self.setWindowTitle('Card Preview')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TintedBackground, True)

        self.setStyleSheet("QDialog {border-radius: 10px;}")

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setOffset(-1, 1)
        self.shadow.setColor(QColor(0, 0, 0))
        self.setGraphicsEffect(self.shadow)

        # self.setWindowOpacity(0.9)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        font_id = QFontDatabase.addApplicationFont("front/Osterbar.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        custom_font = QFont(font_family[0], 50)  # Указываем размер шрифта

        layout = QVBoxLayout()

        self.pic = QLabel(self)
        self.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if type_ in ['program', 'weapon', 'action']:
            self.resize(690, 420)
            width = 660
            height = 420
        else:
            self.resize(430, 750)
            width = 420
            height = 660

        self.pic.setPixmap(QPixmap(im_path).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.pic)

        if type_ == 'action':
            style = ('QPushButton {border-radius: 5px;}'
                     'QPushButton:hover {border: 3px solid rgb(210, 190, 15);}'
                     'QPushButton:pressed {background-color: rgba(70, 100, 180, 100); border: 3px solid rgb(210, 190, 15);}')
            if im_path == 'cards/front/46.png':
                self.loyalty = QPushButton('', self)
                self.loyalty.clicked.connect(self.without_weapon)
                self.loyalty.setGeometry(80, 125, 500, 60)
                self.loyalty.setStyleSheet(style)

                self.weapon = QPushButton('', self)
                self.weapon.clicked.connect(self.without_weapon)
                self.weapon.setGeometry(80, 180, 500, 80)
                self.weapon.setStyleSheet(style)

                self.program = QPushButton('', self)
                self.program.clicked.connect(self.without_weapon)
                self.program.setGeometry(80, 255, 500, 35)
                self.program.setStyleSheet(style)

            elif im_path == 'cards/front/46-1.png':
                self.drop = QPushButton('', self)
                self.drop.clicked.connect(self.with_weapon)
                self.drop.setGeometry(80, 110, 500, 58)
                self.drop.setStyleSheet(style)

                self.change = QPushButton('', self)
                self.change.clicked.connect(self.with_weapon)
                self.change.setGeometry(80, 165, 500, 75)
                self.change.setStyleSheet(style)

                self.shot = QPushButton('', self)
                self.shot.clicked.connect(self.with_weapon)
                self.shot.setGeometry(80, 237, 500, 73)
                self.shot.setStyleSheet(style)

        self.l_text = QLabel(desc)
        self.l_text.setFont(custom_font1)  # Применяем кастомный шрифт
        self.l_text.setStyleSheet("""
            QLabel {
                text-align: center; /* Выравнивание текста влево */
                color: white; /* Цвет текста */
                padding-left: 27px; /* Отступ слева */
                padding-right: 27px; /* Отступ справа */
            }
        """)
        layout.addWidget(self.l_text)

        button_layout = QHBoxLayout()

        self.button = QPushButton('Закрыть')
        self.button.clicked.connect(self.quit)
        self.button.setFont(custom_font)  # Применяем кастомный шрифт
        self.button.setStyleSheet("""
            QPushButton {
                text-align: center; /* Выравнивание текста влево */
                background-color: transparent; /* Убирает фон */
                border: none; /* Убирает границы */
                color: orange; /* Цвет текста */
            }
            QPushButton:hover {
                color: orange; /* Цвет текста при наведении остается черным */
            }
            QPushButton:pressed {
                color: black; /* Цвет текста при нажатии остается черным */
            }
        """)
        button_layout.addWidget(self.button)

        if type_ == 'action':
            self.next = QPushButton('Закончить ход')
            self.next.clicked.connect(self.turn_to_next)
            self.next.setFont(custom_font)  # Применяем кастомный шрифт
            self.next.setStyleSheet("""
                QPushButton {
                    text-align: center; /* Выравнивание текста влево */
                    background-color: transparent; /* Убирает фон */
                    border: none; /* Убирает границы */
                    color: orange; /* Цвет текста */
                }
                QPushButton:hover {
                    color: orange; /* Цвет текста при наведении остается черным */
                }
                QPushButton:pressed {
                    color: black; /* Цвет текста при нажатии остается черным */
                }
            """)
            button_layout.addWidget(self.next)

        layout.addLayout(button_layout)

        self.setLayout(layout)


    def without_weapon(self):
        if self.sender() == self.loyalty:
            self.actionButton.emit({'without_weapon': 'loyalty'})
        elif self.sender() == self.weapon:
            self.actionButton.emit({'without_weapon': 'weapon'})
        elif self.sender() == self.program:
            self.actionButton.emit({'without_weapon': 'program'})

    def with_weapon(self):
        if self.sender() == self.drop:
            self.actionButton.emit({'with_weapon': 'drop'})
        elif self.sender() == self.change:
            self.actionButton.emit({'with_weapon': 'change'})
        elif self.sender() == self.shot:
            self.actionButton.emit({'with_weapon': 'shot'})

    def turn_to_next(self):
        self.goNext.emit()
        self.close()

    def quit(self):
        self.close()


class CardScene(QGraphicsScene):
    actionButton = pyqtSignal(dict)
    goNext = pyqtSignal()

    def __init__(self, name, param, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 1920, 1080)  # Размер сцены

        # Добавляем фон
        self.background_item = QGraphicsPixmapItem(QPixmap("front/game_back.png"))
        self.background_item.setZValue(-1)  # Устанавливаем фон позади всех элементов
        self.addItem(self.background_item)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, Card):
            if event.button() == event.button().LeftButton:
                if not item.hided:
                    item.flip()
            elif event.button() == event.button().MiddleButton:
                item.rotate_90()
            elif event.button() == event.button().RightButton:
                if item.is_open or item.type == 'action':
                    self.show_card_preview(item)
        super().mousePressEvent(event)

    def show_card_preview(self, card):
        if card.is_open:
            img = card.front
        else:
            img = card.back
        # if card.hided:
        dialog = CardPreviewDialog(img, card.description, card.type)
        dialog.actionButton.connect(self.send_action)
        dialog.goNext.connect(self.send_next)
        dialog.exec()


    def send_action(self, action):
        self.actionButton.emit(action)

    def send_next(self):
        self.goNext.emit()


class Game(QWidget):
    sendMessage = pyqtSignal(dict)

    def __init__(self, name, param):
        super().__init__()
        self.setWindowTitle(name)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.parent = main

        self.name = name
        self.addr = param[0]
        self.left = param[1]
        self.opposite = param[2]
        self.right = param[3]
        self.first = param[4]
        print(self.first)
        self.counter_to_action = 0
        self.start_to_action = False

        with open('card_data.json', 'r', encoding='utf-8') as file:
            self.card_data = json.load(file)

        self.pos = self.card_data['pos']

        self.cards = {
            'center': {
                'pistol': None, 'rifle': None, 'launcher': None, 'laser': None},
            'self': {
                'role': None, 'loyalty': [None, None], 'program': [None, None], 'weapon': None, 'action': None},
            'left': {
                'role': None, 'loyalty': [None, None], 'program': [None, None], 'weapon': None, 'action': None},
            'opposite': {
                'role': None, 'loyalty': [None, None], 'program': [None, None], 'weapon': None, 'action': None},
            'right': {
                'role': None, 'loyalty': [None, None], 'program': [None, None], 'weapon': None, 'action': None}}

        self.card_to_send = deepcopy(self.cards)
        self.card_to_receive = deepcopy(self.cards)

        layout = QVBoxLayout()

        field = QGraphicsView()
        field.setRenderHint(field.renderHints() | QPainter.RenderHint.Antialiasing)
        # field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene = CardScene(name, param)
        self.scene.actionButton.connect(self.do_game_action)
        self.scene.goNext.connect(self.send_to_next)
        field.setScene(self.scene)

        layout.addWidget(field)

        self.setLayout(layout)

        # self.action_card = self.create_card('action', 'action', 'action', 'action', False, None)

        self.start()

    def set_table_center(self):
        for type_ in self.cards['center']:
            self.cards['center'][type_] = self.create_card('center', 'weapon', type_, type_, False, None)

    def deal(self):
        if list(self.first.keys())[0] == self.name:
            role_pool = [25, 30, 42, 45] + sample([13, 17], 1)
            loyalty_pool = [47] * 3 + [56] * 2 + [54, 62, 68]
            program_pool = [72, 75, 79, 98]

            for player in self.cards:
                hide = False
                if player in ['left', 'opposite', 'right']:
                    # hide = True
                    pass
                for type_ in self.cards[player]:
                    if type_ == 'role':
                        r_i = sample(role_pool, 1)[0]
                        role_pool.remove(r_i)
                        self.cards[player][type_] = self.create_card(player, type_, type_, r_i, hide, None)
                        self.card_to_send[player][type_] = (player, type_, type_, r_i, hide, None)
                    elif type_ == 'loyalty':
                        l_i1 = sample(loyalty_pool, 1)[0]
                        loyalty_pool.remove(l_i1)
                        l_i2 = sample(loyalty_pool, 1)[0]
                        loyalty_pool.remove(l_i2)
                        self.cards[player][type_][0] = self.create_card(player, type_, type_, l_i1, hide, 0)
                        self.card_to_send[player][type_][0] = (player, type_, type_, l_i1, hide, 0)
                        self.cards[player][type_][1] = self.create_card(player, type_, type_, l_i2, hide, 1)
                        self.card_to_send[player][type_][1] = (player, type_, type_, l_i2, hide, 1)
                    elif type_ == 'program':
                        p_i = sample(program_pool, 1)[0]
                        program_pool.remove(p_i)
                        self.cards[player][type_][0] = self.create_card(player, type_, type_, p_i, hide, 0)
                        self.card_to_send[player][type_][0] = (player, type_, type_, p_i, hide, 0)
                        # 1111111111
                        # self.cards[player][type_][1] = self.create_card(player, type_, type_, p_i, hide, 1)
                        # self.card_to_send[player][type_][1] = (player, type_, type_, p_i, hide, 1)
                    elif type_ == 'action':
                        if player == 'self':
                            self.cards[player][type_] = self.create_card(player, type_, type_, type_, hide, None)
                            self.card_to_send[player][type_] = (player, type_, type_, type_, hide, None)

            message = {'purpose': 'deal_sync',
                       'message': self.card_to_send,
                       'from': f'{self.addr[0]}:{self.addr[1]}',
                       'name': self.name}

            self.send_message(message)
            self.anim_deal()

    def create_card(self, player, card_type, type_, id_, hide, order):
        try:
            card = Card(player, card_type, type_, self.pos, self.card_data[card_type][str(id_)], hide, order)
            self.scene.addItem(card)
            return card
        except Exception as e:
            print(e, '|create_card')

    def anim_deal(self):
        def setup_timer(card, delay):
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(card.move_to_default)
            timer.start(delay)

        timer_ = QTimer(self)
        timer_.setSingleShot(True)
        timer_.timeout.connect(self.to_send_on_deal)
        timer_.start(6000)

        counter = 1
        for player in self.cards:
            for type_ in self.cards[player]:
                cards_to_animate = self.cards[player][type_]
                if isinstance(cards_to_animate, list):
                    for item in cards_to_animate:
                        if item:
                            setup_timer(item, counter * 300)
                            counter += 1
                elif cards_to_animate:
                    setup_timer(cards_to_animate, counter * 300)
                    counter += 1

    def to_send_on_deal(self):
        self.check_for_action()
        message = {'purpose': 'fin_deal',
                   'message': '',
                   'from': f'{self.addr[0]}:{self.addr[1]}',
                   'name': self.name}
        self.send_message(message)

    def check_for_action(self):
        self.counter_to_action += 1
        print(self.counter_to_action, 'action')
        if self.counter_to_action == 4:
            self.start_to_action = True

    def send_to_next(self):
        self.action_handler()
        message = {'purpose': 'next',
                   'message': '',
                   'from': f'{self.addr[0]}:{self.addr[1]}',
                   'name': self.name}
        self.send_message(message)

    def message_handler(self, message):
        try:
            if message['purpose'] == 'deal_sync':
                print(self.name)
                print(self.left)
                print(self.opposite)
                print(self.right)
                # cards = deepcopy(self.cards)
                data = message['message']

                name_to_position = {
                    list(self.left.keys())[0]: ('left', 'opposite', 'right', 'self'),
                    list(self.opposite.keys())[0]: ('opposite', 'right', 'self', 'left'),
                    list(self.right.keys())[0]: ('right', 'self', 'left', 'opposite')}

                if message['name'] in name_to_position:
                    positions = name_to_position[message['name']]
                    self.card_to_receive['self'] = data[positions[0]]
                    self.card_to_receive['left'] = data[positions[1]]
                    self.card_to_receive['opposite'] = data[positions[2]]
                    self.card_to_receive['right'] = data[positions[3]]

                for player in self.cards:
                    if player != 'center':
                        for type_ in self.cards[player]:
                            if type_ == 'role':
                                self.cards[player][type_] = self.create_card(player, *self.card_to_receive[player][type_][1:])
                                # self.card_to_send[player][type_] = ((1130, 355), self.pos[player][type_], type_, r_i, r_offset, hide)
                            elif type_ == 'loyalty':
                                self.cards[player][type_][0] = self.create_card(player, *self.card_to_receive[player][type_][0][1:])
                                # self.card_to_send[player][type_][0] = ((1130, 355), self.pos[player][type_][0], type_,  l_i1, r_offset, hide)
                                self.cards[player][type_][1] = self.create_card(player, *self.card_to_receive[player][type_][1][1:])
                                # self.card_to_send[player][type_][1] = ((1130, 355), self.pos[player][type_][1], type_,  l_i2, r_offset, hide)
                            elif type_ == 'program':
                                if self.card_to_receive[player][type_][0] is not None:
                                    self.cards[player][type_][0] = self.create_card(player, *self.card_to_receive[player][type_][0][1:])
                                if self.card_to_receive[player][type_][1] is not None:
                                    self.cards[player][type_][1] = self.create_card(player, *self.card_to_receive[player][type_][1][1:])
                                # self.card_to_send[player][type_][0] = ((1090, 545), self.pos[player][type_][0], type_, p_i, r_offset, hide)
                            elif type_ == 'action':
                                if self.card_to_receive[player][type_] is not None:
                                    self.cards[player][type_] = self.create_card(player, *self.card_to_receive[player][type_][1:])
                                    if player != 'self':
                                        self.cards[player][type_].hided = True
                self.anim_deal()

                print(message, 444444444)
            elif message['purpose'] == 'fin_deal':
                print('получил действо')
                self.check_for_action()
            elif message['purpose'] == 'next':
                print('перешёл')
                self.action_handler()
        except Exception as e:
            print(e, '|message_handler')
        # self.cards = message['message']

    def action_handler(self):
        player_ = next((player for player in self.cards if self.cards[player].get('action') is not None), None)

        if player_:
            targets = {'self': 'left', 'left': 'opposite', 'opposite': 'right', 'right': 'self'}
            target = targets[player_]

            self.cards[target]['action'] = self.cards[player_]['action']
            self.cards[player_]['action'] = None
            self.cards[target]['action'].player = target
            self.cards[target]['action'].move_action()
            if target == 'self':
                self.cards[target]['action'].hided = False
        # player_ = None
        # for player in self.cards:
        #     for type_ in self.cards[player]:
        #         if type_ == 'action' and self.cards[player][type_] is not None:
        #             player_ = player
        # if player_ == 'self':
        #     self.cards['left']['action'] = self.cards[player_]['action']
        #     self.cards[player_]['action'] = None
        #     self.cards['left']['action'].player = 'left'
        #     self.cards['left']['action'].move_action()
        #
        # elif player_ == 'left':
        #     self.cards['opposite']['action'] = self.cards[player_]['action']
        #     self.cards[player_]['action'] = None
        #     self.cards['opposite']['action'].player = 'opposite'
        #     self.cards['opposite']['action'].move_action()
        #
        # elif player_ == 'opposite':
        #     self.cards['right']['action'] = self.cards[player_]['action']
        #     self.cards[player_]['action'] = None
        #     self.cards['right']['action'].player = 'right'
        #     self.cards['right']['action'].move_action()
        #
        # elif player_ == 'right':
        #     self.cards['self']['action'] = self.cards[player_]['action']
        #     self.cards[player_]['action'] = None
        #     self.cards['self']['action'].player = 'self'
        #     self.cards['self']['action'].move_action()

    def do_game_action(self, action):
        if list(action.keys())[0] == 'without_weapon':
            if action[list(action.keys())[0]] == 'loyalty':

                print(1)
            elif action[list(action.keys())[0]] == 'weapon':
                print(2)
            elif action[list(action.keys())[0]] == 'program':
                print(3)
        elif list(action.keys())[0] == 'with_weapon':
            if action[list(action.keys())[0]] == 'drop':
                print(4)
            elif action[list(action.keys())[0]] == 'change':
                print(5)
            elif action[list(action.keys())[0]] == 'shot':
                print(6)

    def send_message(self, message):
        self.sendMessage.emit(message)

    def start(self):
        self.set_table_center()
        self.deal()

    #
    # def start_action(self):
    #     self.

    # def closeEvent(self, event):
    #     self.exit()
    #
    # def exit(self):
    #     self.parent.show()
    #     self.close()


if __name__ == "__main__":
    app = QApplication([])
    window = Game('444', [('172.19.0.1', 61012), {'333': '172.19.0.1:61010'}, {'111': '172.19.0.1:61009'}, {'222': '172.19.0.1:61011'}, {'444': '172.19.0.1:61012'}])
    window.show()
    app.exec()
