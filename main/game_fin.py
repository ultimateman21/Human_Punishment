from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, \
     QGraphicsTextItem, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont, QPixmap, QImage, QTransform, QPalette, QBrush, QColor, QPainter
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QVariantAnimation, pyqtSignal

from random import sample
from copy import deepcopy
from PIL import Image
from json import load

from PyQt6.QtWidgets import QApplication


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
        self.action_done = False

        self.offset = {'center': 0, 'self': 0, 'left': 90, 'opposite': 180, 'right': 270}
        self.action_previous = {'self': 'right', 'left': 'self', 'opposite': 'left', 'right': 'opposite'}

        if self.card_type in ['program', 'weapon', 'action']:
            self.width = 220
            self.height = 140
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
        self.setPos(QPointF(*self.pos['center'][self.type]))

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

    def move_action(self, from_):
        # self.move_to(self.pos[self.action_previous[self.player]]['action'], self.pos[self.player]['action'], self.rotate_action)
        self.move_to(self.pos[from_]['action'], self.pos[self.player]['action'], lambda f=from_: self.rotate_action(f))

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

    def rotate_action(self, from_):
        if self.player != 'self':
            # self.rotate_to(self.offset[self.action_previous[self.player]], self.offset[self.player])
            self.rotate_to(self.offset[from_], self.offset[self.player])
        else:
            # self.rotate_to(self.offset[self.action_previous[self.player]], 360)
            self.rotate_to(self.offset[from_], 360)

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

    def __init__(self, card):
        super().__init__()
        try:
            self.setWindowTitle('Card Preview')
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

            self.type = 'horizontal' if card.type in ['program', 'pistol', 'rifle', 'launcher', 'laser', 'action'] else 'vertical'
            size_map = {'horizontal': [(765, 600), (607, 420)], 'vertical': [(575, 740), (419, 607)]}
            self.setFixedSize(*size_map[self.type][0])

            font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            custom_font = QFont(font_family[0], 40)
            custom_font1 = QFont(font_family[0], 20)

            self.card = card

            if self.card.is_open:
                im_path = self.card.front
            else:
                im_path = self.card.back

            layout = QVBoxLayout(self)
            container = QWidget()
            container.setStyleSheet('background-color: rgba(0, 0, 0, 128); border-radius: 20px;')
            container.setContentsMargins(20, 20, 20, 20)
            layout_ = QHBoxLayout(container)
            control_layout = QVBoxLayout()

            self.quit_button = QPushButton()
            self.quit_button.setFixedSize(70, 70)
            self.white_cross_icon = QPixmap('../source/design/cross_white.png')
            self.gray_cross_icon = QPixmap('../source/design/cross_gray.png')
            self.black_cross_icon = QPixmap('../source/design/cross_black.png')
            self.quit_button.paintEvent = self.quit_button_icon_handler
            self.quit_button.clicked.connect(self.quit)
            control_layout.addWidget(self.quit_button, Qt.AlignmentFlag.AlignTop)
            control_layout.addStretch(0)

            if self.card.type == 'action':
                self.turn_next_button = QPushButton('Закончить ход')
                self.turn_next_button.setFixedSize(47, 220)
                self.turn_next_button.setFont(custom_font)
                self.turn_next_button.paintEvent = self.draw_turn_next_button
                self.turn_next_button.clicked.connect(self.turn_to_next)
                control_layout.addWidget(self.turn_next_button, Qt.AlignmentFlag.AlignBottom)

            layout_.addLayout(control_layout)

            content_layout = QVBoxLayout()

            self.pic = QWidget()
            self.pic.setFixedSize(*size_map[self.type][1])
            self.img = QPixmap(im_path).scaled(*size_map[self.type][1], Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            self.pic.paintEvent = self.draw_card

            if self.card.type == 'action' and not self.card.action_done:
                style = ('QPushButton {background-color: transparent; border-radius: 5px;}'
                         'QPushButton:hover {border: 3px solid rgb(210, 190, 15);}'
                         'QPushButton:pressed {background-color: rgba(70, 100, 180, 100); border: 3px solid rgb(210, 190, 15);}')

                button_config = {'../source/cards/front/46.png': [((37, 115, 500, 57), 'without_weapon', 'loyalty'),
                                                                  ((37, 170, 500, 76), 'without_weapon', 'weapon'),
                                                                  ((37, 244, 500, 33), 'without_weapon', 'program')],
                                 '../source/cards/front/46-1.png': [((37, 101, 500, 56), 'with_weapon', 'drop'),
                                                                    ((37, 155, 500, 75), 'with_weapon', 'change'),
                                                                    ((37, 228, 500, 73), 'with_weapon', 'shot')]}

                for pos, group, signal in button_config[im_path]:
                    button = QPushButton(self.pic)
                    button.setGeometry(*pos)
                    button.setStyleSheet(style)
                    button.clicked.connect(lambda _, g=group, s=signal: self.send_action({g: s}))

            content_layout.addWidget(self.pic)

            self.l_text = QLabel(self.card.description)
            self.l_text.setWordWrap(True)
            self.l_text.setFont(custom_font1)
            self.l_text.setStyleSheet('background-color: transparent; color: white;')
            content_layout.addWidget(self.l_text)

            layout_.addLayout(content_layout)
            layout.addWidget(container)
        except Exception as e:
            print(e, '|dialog')

    def quit_button_icon_handler(self, event):
        painter = QPainter(self.quit_button)
        icon = (self.black_cross_icon if self.quit_button.isDown() else
                self.gray_cross_icon if self.quit_button.underMouse() else self.white_cross_icon)
        icon_rect = icon.rect()
        icon_rect.moveTopLeft(self.quit_button.rect().topLeft() - QPoint(6, 6))
        painter.drawPixmap(icon_rect, icon)
        painter.end()

    def draw_turn_next_button(self, event):
        painter = QPainter(self.turn_next_button)
        text_color = QColor('black' if self.turn_next_button.isDown() else 'gray' if self.turn_next_button.underMouse() else 'white')
        painter.setPen(text_color)
        painter.rotate(270)
        painter.drawText(-self.turn_next_button.height(), self.turn_next_button.width() - 5, self.turn_next_button.text())
        painter.end()

    def draw_card(self, event):
        painter = QPainter(self.pic)
        painter.drawPixmap(self.pic.rect(), self.img)
        painter.end()

    def send_action(self, action):
        print('send_action')
        self.actionButton.emit(action)
        self.card.action_done = True
        self.quit()

    def turn_to_next(self):
        self.goNext.emit()
        self.close()

    def quit(self):
        self.close()


class CardScene(QGraphicsScene):
    actionButton = pyqtSignal(dict)
    goNext = pyqtSignal()
    oneFlip = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, 1920, 1078)  # Размер сцены
        self.one_flip = False

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, Card):
            if event.button() == event.button().LeftButton:
                if not item.hided:
                    item.flip()
                    if self.one_flip and item.player != 'self':
                        self.oneFlip.emit()
                        self.one_flip = False
            elif event.button() == event.button().MiddleButton:
                item.rotate_90()
            elif event.button() == event.button().RightButton:
                if item.is_open or (item.type == 'action' and item.player == 'self'):
                    self.show_card_preview(item)
        super().mousePressEvent(event)

    def show_card_preview(self, card):
        dialog = CardPreviewDialog(card)
        dialog.actionButton.connect(self.send_action)
        dialog.goNext.connect(self.send_next)
        dialog.exec()

    def send_action(self, action):
        self.actionButton.emit(action)

    def send_next(self):
        self.goNext.emit()


class Game(QWidget):
    sendMessage = pyqtSignal(dict)

    def __init__(self, main, name, param):
        super().__init__()
        self.setWindowTitle(f'Судный день - {name}')
        self.showFullScreen()

        self.parent = main

        self.name = name
        self.addr = param[0]
        self.left = param[1]
        self.opposite = param[2]
        self.right = param[3]
        self.first = param[4]
        print(self.first, self.name, self.left, self.opposite, self.right)
        self.counter_to_action = 0
        self.start_to_action = False

        font_id = QFontDatabase.addApplicationFont('../source/design/Osterbar.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        self.custom_font = QFont(font_family[0], 20)

        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap('../source/design/game_back.png')))
        self.setPalette(palette)

        with open('../source/card_data.json', 'r', encoding='utf-8') as file:
            self.card_data = load(file)

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

        self.death = {'self': False, 'left': False, 'opposite': False, 'right': False}

        self.card_to_send = deepcopy(self.cards)
        self.card_to_receive = deepcopy(self.cards)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        field = QGraphicsView()
        field.setStyleSheet('background-color: transparent;')
        field.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        field.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene = CardScene()
        self.scene.actionButton.connect(self.do_game_action)
        self.scene.goNext.connect(self.send_to_next)
        self.scene.oneFlip.connect(self.hide_all)
        field.setScene(self.scene)

        layout.addWidget(field)
        # self.start()

    def set_table_center(self):
        for type_ in self.cards['center']:
            self.cards['center'][type_] = self.create_card('center', 'weapon', type_, type_, False, None)

    def set_names(self):
        directions = [{'key': 'self', 'name': self.name, 'rotation': 0},
                      {'key': 'left', 'name': list(self.left.keys())[0], 'rotation': 90},
                      {'key': 'opposite', 'name': list(self.opposite.keys())[0], 'rotation': 0},
                      {'key': 'right', 'name': list(self.right.keys())[0], 'rotation': 270}]

        for direction in directions:
            name_item = QGraphicsTextItem(direction['name'])
            name_item.setFont(self.custom_font)
            name_item.setDefaultTextColor(Qt.GlobalColor.white)

            rect = self.pos[direction['key']]['name']
            if direction['key'] == 'self':
                name_item.setPos(rect[0][0] + rect[1][0] - name_item.boundingRect().width(), rect[0][1])
            elif direction['key'] == 'left':
                name_item.setPos(rect[0][0], rect[0][1] + rect[1][0] - name_item.boundingRect().width())
                name_item.setRotation(direction['rotation'])
            elif direction['key'] == 'opposite':
                name_item.setPos(rect[0][0], rect[0][1])
            elif direction['key'] == 'right':
                name_item.setPos(rect[0][0], rect[0][1] + name_item.boundingRect().width())
                name_item.setRotation(direction['rotation'])
            self.scene.addItem(name_item)

    def deal(self):
        if list(self.first.keys())[0] == self.name:
            role_pool = [25, 30, 42, 45] + sample([13, 17], 1)
            loyalty_pool = [47] * 3 + [56] * 2 + [54, 62, 68]
            program_pool = [72, 75, 79, 98]

            for player in self.cards:
                hide = False
                if player in ['left', 'opposite', 'right']:
                    hide = True
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
                    list(self.left.keys())[0]: ('right', 'self', 'left', 'opposite'),
                    list(self.opposite.keys())[0]: ('opposite', 'right', 'self', 'left'),
                    list(self.right.keys())[0]: ('left', 'opposite', 'right', 'self')}

                if message['name'] in name_to_position:
                    positions = name_to_position[message['name']]
                    self.card_to_receive['self'] = data[positions[0]]
                    self.card_to_receive['left'] = data[positions[1]]
                    self.card_to_receive['opposite'] = data[positions[2]]
                    self.card_to_receive['right'] = data[positions[3]]

                for player in self.cards:
                    if player != 'center':
                        hide = True
                        if player == 'self':
                            hide = False
                        for type_ in self.cards[player]:
                            if type_ == 'role':
                                self.cards[player][type_] = self.create_card(player, *self.card_to_receive[player][type_][1:])
                                self.cards[player][type_].hided = hide
                                # self.card_to_send[player][type_] = ((1130, 355), self.pos[player][type_], type_, r_i, r_offset, hide)
                            elif type_ == 'loyalty':
                                self.cards[player][type_][0] = self.create_card(player, *self.card_to_receive[player][type_][0][1:])
                                self.cards[player][type_][0].hided = hide
                                # self.card_to_send[player][type_][0] = ((1130, 355), self.pos[player][type_][0], type_,  l_i1, r_offset, hide)
                                self.cards[player][type_][1] = self.create_card(player, *self.card_to_receive[player][type_][1][1:])
                                self.cards[player][type_][1].hided = hide
                                # self.card_to_send[player][type_][1] = ((1130, 355), self.pos[player][type_][1], type_,  l_i2, r_offset, hide)
                            elif type_ == 'program':
                                if self.card_to_receive[player][type_][0] is not None:
                                    self.cards[player][type_][0] = self.create_card(player, *self.card_to_receive[player][type_][0][1:])
                                    self.cards[player][type_][0].hided = hide
                                if self.card_to_receive[player][type_][1] is not None:
                                    self.cards[player][type_][1] = self.create_card(player, *self.card_to_receive[player][type_][1][1:])
                                    self.cards[player][type_][1].hided = hide
                                # self.card_to_send[player][type_][0] = ((1090, 545), self.pos[player][type_][0], type_, p_i, r_offset, hide)
                            elif type_ == 'action':
                                if self.card_to_receive[player][type_] is not None:
                                    self.cards[player][type_] = self.create_card(player, *self.card_to_receive[player][type_][1:])
                                    self.cards[player][type_].hided = hide
                self.anim_deal()
            elif message['purpose'] == 'fin_deal':
                self.check_for_action()
            elif message['purpose'] == 'next':
                self.action_handler()
        except Exception as e:
            print(e, '|message_handler')

    def action_handler(self):
        player_ = next((player for player in self.cards if self.cards[player].get('action') is not None), None)

        if player_:
            targets = {'self': 'left', 'left': 'opposite', 'opposite': 'right', 'right': 'self'}
            target = targets[player_]

            while self.death.get(target, False):
                target = targets[target]

            self.cards[target]['action'] = self.cards[player_]['action']
            if target != 'self':
                self.cards[target]['action'].hided = True
            else:
                self.cards[target]['action'].hided = False
            self.cards[player_]['action'] = None
            self.cards[target]['action'].action_done = False
            self.cards[target]['action'].player = target
            self.cards[target]['action'].move_action(player_)
            self.close_all_card()
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
                print(1, 1)
                for player in self.cards:
                    if player not in ['self', 'center']:
                        for card in self.cards[player]['loyalty']:
                            card.hided = False
                self.scene.one_flip = True
            elif action[list(action.keys())[0]] == 'weapon':
                print(2, 2)
            elif action[list(action.keys())[0]] == 'program':
                print(3, 3)
        elif list(action.keys())[0] == 'with_weapon':
            if action[list(action.keys())[0]] == 'drop':
                print(4, 4)
            elif action[list(action.keys())[0]] == 'change':
                print(5, 5)
            elif action[list(action.keys())[0]] == 'shot':
                print(6, 6)

    def hide_all(self):
        for player in self.cards:
            if player not in ['self', 'center']:
                for type_ in self.cards[player]:
                    if type_ == 'role':
                        self.cards[player]['role'].hided = True
                    elif type_ == 'loyalty':
                        for card in self.cards[player]['loyalty']:
                            card.hided = True

    def close_all_card(self):
        for player in self.cards:
            if player not in ['self', 'center']:
                for type_ in self.cards[player]:
                    if type_ == 'role' and self.cards[player]['role'].is_open:
                        self.cards[player]['role'].flip()
                    elif type_ == 'loyalty':
                        for card in self.cards[player]['loyalty']:
                            if card.is_open:
                                card.flip()

    def send_message(self, message):
        self.sendMessage.emit(message)

    def start(self):
        self.set_table_center()
        self.set_names()
        self.deal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_0:
            print(666)
            self.scene.update()

    #
    # def start_action(self):
    #     self.

    def closeEvent(self, event):
        self.exit()

    def exit(self):
        self.parent.show()
        self.close()


# if __name__ == "__main__":
#     app = QApplication([])
#     window = Game('444', [('172.19.0.1', 61012), {'333': '172.19.0.1:61010'}, {'111': '172.19.0.1:61009'}, {'222': '172.19.0.1:61011'}, {'444': '172.19.0.1:61012'}])
#     window.show()
#     app.exec()
