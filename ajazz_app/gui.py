from ajazz_app.i18n import STRINGS
import threading
from datetime import datetime
import json
import os
import time
from PySide6.QtCore import Qt, QTimer, QEvent, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPixmap, QPainter, QIcon, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget,
    QComboBox, QCheckBox, QMessageBox, QDialog, QGraphicsOpacityEffect, QInputDialog, QGroupBox, QListWidget, QListView, QFrame
)
from .core import AjazzController, EFFECTS
from .keymap import ROWS
from .widgets import RotaryKnob

DARK_STYLE = """
QWidget { background-color: #111318; color: #e2e2e9; font-family: "Inter", "Roboto", "Segoe UI", sans-serif; font-size: 13px; }
QFrame#sidebar { background-color: #181a20; border-right: 1px solid #262932; }
QPushButton#nav_btn { background: transparent; border: none; border-radius: 20px; padding: 11px 16px; margin: 2px 10px; text-align: left; font-size: 13px; font-weight: 500; color: #9ea3b0; }
QPushButton#nav_btn:hover { background-color: #23262f; color: #ffffff; }
QPushButton#nav_btn:checked { background-color: #004a77; color: #c2e7ff; font-weight: 600; }
QPushButton { background-color: #22252e; border: 1px solid #323642; border-radius: 8px; padding: 6px 12px; color: #e2e2e9; font-weight: 500; }
QPushButton:hover { background-color: #2b2f3a; border-color: #a8c7fa; }
QPushButton#keycap { background-color: #20232c; border: 1px solid #313542; border-bottom: 2px solid #14161c; border-radius: 6px; padding: 0px; font-size: 11px; font-weight: 500; color: #d5d8e2; }
QPushButton#keycap:hover { border-color: #a8c7fa; background-color: #282c37; color: #ffffff; }
QPushButton#primary { background-color: #a8c7fa; color: #062e6f; font-weight: 700; border: none; border-radius: 18px; padding: 9px 24px; }
QPushButton#primary:hover { background-color: #c2d9ff; }
QFrame#card { background-color: #181a20; border: 1px solid #262932; border-radius: 16px; }
QLabel#card_title { color: #a8c7fa; font-size: 13px; font-weight: 700; padding-bottom: 6px; }
QComboBox { combobox-popup: 0; }
QComboBox, QListWidget { background-color: #22252e; border: 1px solid #323642; border-radius: 8px; padding: 6px 28px 6px 12px; color: #e2e2e9; selection-background-color: #004a77; selection-color: #c2e7ff; }
QComboBox:disabled, QPushButton:disabled, QPushButton#primary:disabled { background-color: #1c1f27; border: 1px solid #262932; color: #5f6368; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 17px; height: 17px; border-radius: 5px; border: 1.5px solid #44495a; background-color: #22252e; }
QCheckBox::indicator:hover { border-color: #a8c7fa; }
QCheckBox::indicator:checked { background-color: #a8c7fa; border-color: #a8c7fa; }
QCheckBox::indicator:disabled { background-color: #181a20; border-color: #262932; }
QDialog, QMessageBox, QInputDialog { background-color: #17191f; color: #e2e2e9; dialogbuttonbox-buttons-have-icons: 0; }
QComboBox:hover, QListWidget:hover { border-color: #a8c7fa; background-color: #262a35; }
QComboBox:on { border-color: #a8c7fa; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 26px; border: none; background: transparent; }
QComboBox::down-arrow { image: url("/home/chyo/.config/ajazz_studio/chevron.svg"); width: 12px; height: 12px; }
QComboBoxPrivateContainer { background-color: transparent; border: none; }
QComboBox QAbstractItemView { background-color: #1c1f27; border: 1px solid #a8c7fa; border-top: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; padding: 4px; color: #e2e2e9; outline: none; }
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 10px; border-radius: 6px; }
QComboBox QAbstractItemView::item:hover { background-color: #282d39; color: #ffffff; }
QComboBox QAbstractItemView::item:selected { background-color: #004a77; color: #c2e7ff; font-weight: 600; }
QScrollBar:vertical { background: #181a20; width: 8px; border-radius: 4px; margin: 2px; }
QScrollBar::handle:vertical { background: #383d4c; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #a8c7fa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QCheckBox { spacing: 8px; color: #e2e2e9; font-weight: 500; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #8e9099; background: transparent; }
QCheckBox::indicator:checked { background: #a8c7fa; border-color: #a8c7fa; }
QLabel { background: transparent; }
"""

def make_card(title: str):
    card_lbl = QLabel(title)
    box = QFrame()
    box.setObjectName("card")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(10)
    lbl = QLabel(title)
    lbl.setObjectName("card_title")
    lay.addWidget(lbl)
    return box, lay

class ColorPickerDialog(QDialog):
    def __init__(self, initial: QColor, parent=None, lang='ru'):
        t = STRINGS.get(lang, STRINGS['ru'])
        super().__init__(parent)
        self.setWindowTitle(t["color_title"])
        self.setFixedSize(360, 290)
        self.color = QColor(initial)
        if self.color.value() < 40:
            self.color = QColor(255, 0, 0)
        self._hue = max(0, self.color.hsvHue())
        self._sat = max(0, self.color.hsvSaturation())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(14)

        top = QHBoxLayout()
        self.preview = QFrame()
        self.preview.setFixedSize(44, 44)
        self.hex_lbl = QLabel()
        self.hex_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #e2e2e9;")
        top.addWidget(self.preview)
        top.addSpacing(8)
        top.addWidget(self.hex_lbl)
        top.addStretch()
        lay.addLayout(top)

        self.hue_bar = self._make_bar(self._on_hue)
        self.sat_bar = self._make_bar(self._on_sat)
        lay.addWidget(QLabel(t["hue_lbl"]))
        lay.addWidget(self.hue_bar)
        lay.addWidget(QLabel(t["sat_lbl"]))
        lay.addWidget(self.sat_bar)

        presets = QHBoxLayout()
        presets.setSpacing(6)
        for hx in ("#ff0000", "#ff6d00", "#ffd600", "#76ff03", "#00e676", "#00e5ff", "#0000ff", "#651fff", "#d500f9", "#ff4081", "#ffffff"):
            b = QPushButton()
            b.setFixedSize(24, 24)
            b.setStyleSheet(f"QPushButton {{ background-color: {hx}; border-radius: 12px; border: 1.5px solid #353945; padding: 0; }} QPushButton:hover {{ border-color: #ffffff; }}")
            b.clicked.connect(lambda _, c=hx: self._set_preset(QColor(c)))
            presets.addWidget(b)
        lay.addLayout(presets)

        btns = QHBoxLayout()
        btns.addStretch()
        b_cancel = QPushButton(t["cancel_btn"])
        b_cancel.clicked.connect(self.reject)
        b_ok = QPushButton(t["ok_btn"])
        b_ok.setObjectName("primary")
        b_ok.clicked.connect(self.accept)
        btns.addWidget(b_cancel)
        btns.addWidget(b_ok)
        lay.addLayout(btns)
        self._sync()

    def _make_bar(self, cb):
        lbl = QLabel()
        lbl.setFixedHeight(20)
        lbl.setCursor(Qt.PointingHandCursor)
        lbl.mousePressEvent = lambda e: cb(e.position().x(), lbl.width())
        lbl.mouseMoveEvent = lambda e: cb(e.position().x(), lbl.width()) if e.buttons() & Qt.LeftButton else None
        return lbl

    def _on_hue(self, x, w):
        self._hue = int(max(0, min(359, (x / max(1, w)) * 359)))
        self._sync()

    def _on_sat(self, x, w):
        self._sat = int(max(0, min(255, (x / max(1, w)) * 255)))
        self._sync()

    def _set_preset(self, c: QColor):
        self._hue = max(0, c.hsvHue())
        self._sat = c.hsvSaturation()
        self._sync()

    def _sync(self):
        self.color = QColor.fromHsv(self._hue, self._sat, 255)
        hx = self.color.name().upper()
        self.preview.setStyleSheet(f"background-color: {hx}; border-radius: 12px; border: 1.5px solid #ffffff;")
        self.hex_lbl.setText(hx)

        w, h = 324, 20
        pm_h = QPixmap(w, h)
        pm_h.fill(Qt.transparent)
        pt = QPainter(pm_h)
        pt.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, w, 0)
        for i in range(7):
            grad.setColorAt(i / 6.0, QColor.fromHsv(min(359, i * 60), 255, 255))
        pt.setBrush(grad)
        pt.setPen(Qt.NoPen)
        pt.drawRoundedRect(0, 2, w, h - 4, 8, 8)
        cx = int((self._hue / 359.0) * (w - 12)) + 6
        pt.setPen(QPen(QColor("#ffffff"), 2))
        pt.setBrush(self.color)
        pt.drawEllipse(cx - 6, 3, 12, 12)
        pt.end()
        self.hue_bar.setPixmap(pm_h)

        pm_s = QPixmap(w, h)
        pm_s.fill(Qt.transparent)
        pt = QPainter(pm_s)
        pt.setRenderHint(QPainter.Antialiasing)
        grad_s = QLinearGradient(0, 0, w, 0)
        grad_s.setColorAt(0.0, QColor(255, 255, 255))
        grad_s.setColorAt(1.0, QColor.fromHsv(self._hue, 255, 255))
        pt.setBrush(grad_s)
        pt.setPen(Qt.NoPen)
        pt.drawRoundedRect(0, 2, w, h - 4, 8, 8)
        sx = int((self._sat / 255.0) * (w - 12)) + 6
        pt.setPen(QPen(QColor("#17191f"), 2))
        pt.setBrush(self.color)
        pt.drawEllipse(sx - 6, 3, 12, 12)
        pt.end()
        self.sat_bar.setPixmap(pm_s)


class AjazzWindow(QWidget):
    _prof_done = Signal(str, bool)
    def __init__(self):
        super().__init__()
        self.ctrl = AjazzController()
        self.selected_slot = 0
        self.adv_pair = [(49, 0x04, "A"), (51, 0x07, "D")]
        self.adv_pick_idx = None
        self.cust_pick_step = None
        self.mac_pick_mode = None
        self.dks_pick_mode = None
        if hasattr(self, "btn_dks_target"):
            self.btn_dks_target.setChecked(False)
            self.btn_dks_add.setChecked(False)
            self.btn_dks_target.setText("Выбрать клавишу")
            self.btn_dks_add.setText("Добавить клавиши")
            for b in self.dks_btns:
                b.setChecked(False)
        if hasattr(self, "btn_mac_target"):
            self.btn_mac_target.setChecked(False)
            self.btn_mac_rec.setChecked(False)
            self.btn_mac_target.setText("Выбрать клавишу")
            self.btn_mac_rec.setText("Добавить клавиши")
        self.cust_target = None
        self.cust_keys = []
        self.custom_map = {"normal": {}, "fn": {}}
        self.mac_pick_mode = None
        self.mac_target = None
        self.mac_last_ts = None
        self.dks_pick_mode = None
        self.dks_target = None
        self.dks_keys = [(0, "—"), (0, "—"), (0, "—"), (0, "—")]
        self.slot_info = {s: (l, h) for r in ROWS for l, _, h, s, _ in r if l and s is not None}
        self.key_buttons = {}
        self.qt_key_map = {}
        self.pressed_slots = set()
        self.calibrated_slots = set()
        self.is_calibrating = False
        self._was_connected = False
        self.lang = 'ru'
        self._prof_done.connect(self._on_prof_written)
        self._log_until = 0.0
        self._log_history = []
        QApplication.instance().installEventFilter(self)
        self.nav_buttons = []

        self.setWindowTitle("Ajazz AK820 Max HE")
        self.resize(1220, 760)
        QApplication.instance().setStyleSheet(DARK_STYLE)

        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        main_lay.addWidget(self._build_sidebar())

        right_area = QWidget()
        r_lay = QVBoxLayout(right_area)
        r_lay.setContentsMargins(20, 14, 20, 18)
        r_lay.setSpacing(10)
        r_lay.addLayout(self._build_topbar())
        r_lay.addWidget(self._build_keyboard_preview())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_light_tab())
        self.stack.addWidget(self._build_switch_tab())
        self.stack.addWidget(self._build_adv_tab())
        self.stack.addWidget(self._build_custom_tab())
        self.stack.addWidget(self._build_macro_tab())
        self.stack.addWidget(self._build_dks_tab())
        self.stack.addWidget(self._build_calib_tab())
        r_lay.addWidget(self.stack, 1)

        main_lay.addWidget(right_area, 1)
        for cb in self.findChildren(QComboBox):
            v = QListView()
            cb.setView(v)
            w = v.window()
            w.setWindowFlags(w.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            w.setAttribute(Qt.WA_TranslucentBackground, True)
            orig_show = cb.showPopup
            def make_show(box=cb, popup_w=w, fn=orig_show):
                def _show():
                    fn()
                    popup_w.setWindowOpacity(0.0)
                    anim = QPropertyAnimation(popup_w, b"windowOpacity", popup_w)
                    anim.setDuration(130)
                    anim.setStartValue(0.0)
                    anim.setEndValue(1.0)
                    anim.setEasingCurve(QEasingCurve.OutCubic)
                    anim.start()
                    popup_w._fade_anim = anim
                return _show
            cb.showPopup = make_show()
        self._restore_ui_state()
        self._set_lang(self.lang, save=False)
        self._switch_page(0)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(800)
        self._update_status()

    def _build_sidebar(self):
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(245)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(8, 20, 8, 20)
        lay.setSpacing(4)

        logo = QLabel("  Ajazz AK820 Max HE")
        logo.setStyleSheet("color: #a8c7fa; font-size: 16px; font-weight: 700; padding: 0 8px 16px 8px;")
        lay.addWidget(logo)

        items = [
            "Подсветка и эффекты",
            "Ход свитчей (RT)",
            "Rappy Snappy / SOCD",
            "Custom Keys / MT",
            "Макросы (Shortcuts)",
            "DKS (Динамический ход)",
            "Система и калибровка"
        ]
        for idx, text in enumerate(items):
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            lay.addWidget(btn)
            self.nav_buttons.append(btn)

        tips = [
            "Настройка цвета, яркости, скорости и 19 встроенных эффектов RGB",
            "Настройка глубины срабатывания и чувствительности Fast Trigger",
            "Парные игровые функции Rappy Snappy и SOCD для любых двух клавиш",
            "Переназначение клавиш на слоях Normal/Fn, Mod-Tap и Toggle",
            "Запись и привязка последовательностей нажатий с задержками",
            "Dynamic Key Stroke: до 4 действий на разной глубине нажатия одной клавиши",
            "Частота опроса (до 8000 Гц), мёртвые зоны и калибровка датчиков Холла"
        ]
        for btn, tip in zip(self.nav_buttons, tips):
            btn.setToolTip(tip)
        lay.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("border: none; background-color: #252832; margin: 0px 16px;")
        lay.addWidget(sep)

        self.chk_pro = QCheckBox("Сашенька, ты ювелир!")
        self.chk_pro.setStyleSheet("QCheckBox { padding-top: 10px; spacing: 8px; color: #c4c6d0; font-weight: 500; }")
        self.chk_pro.setToolTip("Ювелирная настройка всех крутилок глубины и чувствительности с шагом 0.01 мм")
        self.chk_pro.toggled.connect(self._toggle_pro_mode)
        pro_row = QHBoxLayout()
        pro_row.addStretch()
        pro_row.addWidget(self.chk_pro)
        pro_row.addStretch()
        lay.addLayout(pro_row)

        return side

    def _switch_page(self, idx: int):
        if self.stack.currentIndex() != idx:
            self.stack.setCurrentIndex(idx)
            w = self.stack.currentWidget()
            if w:
                eff = QGraphicsOpacityEffect(w)
                w.setGraphicsEffect(eff)
                anim = QPropertyAnimation(eff, b"opacity", w)
                anim.setDuration(150)
                anim.setStartValue(0.35)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.finished.connect(lambda: w.setGraphicsEffect(None))
                anim.start()
                w._page_anim = anim
        else:
            self.stack.setCurrentIndex(idx)
        self.adv_pick_idx = None
        self.cust_pick_step = None
        if hasattr(self, "btn_cust_pick"):
            self.btn_cust_pick.setChecked(False)
            self._sync_cust_btns()
        if hasattr(self, "btn_adv_pick"):
            self.btn_adv_pick.setChecked(False)
            self._sync_adv_pair_btns()
        self._refresh_key_styles()
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == idx)

    def _build_topbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.status_lbl = QLabel("Поиск клавиатуры...")
        bar.addWidget(self.status_lbl)
        bar.addStretch()

        self.btn_ru = QPushButton("RU")
        self.btn_en = QPushButton("EN")
        for code, b in (("ru", self.btn_ru), ("en", self.btn_en)):
            b.setCheckable(True)
            b.setFixedSize(38, 28)
            b.setStyleSheet("QPushButton { padding: 2px 4px; border-radius: 10px; font-size: 11px; } QPushButton:checked { background-color: #004a77; border: 1px solid #a8c7fa; color: #ffffff; }")
            b.clicked.connect(lambda _, c=code: self._set_lang(c))
            bar.addWidget(b)
        self.btn_ru.setChecked(True)
        bar.addSpacing(10)

        self.lbl_prof = QLabel("Профиль:")
        bar.addWidget(self.lbl_prof)
        self.cb_profiles = QComboBox()
        self.cb_profiles.setMinimumWidth(160)
        self.cb_profiles.setToolTip("Список сохранённых профилей настроек")
        bar.addWidget(self.cb_profiles)

        self.btn_prof_load = QPushButton("Загрузить")
        self.btn_prof_load.setToolTip("Загрузить выбранный профиль в интерфейс и записать его в клавиатуру")
        self.btn_prof_load.clicked.connect(self._on_load_profile)
        bar.addWidget(self.btn_prof_load)

        self.btn_prof_save = QPushButton("Сохранить...")
        self.btn_prof_save.setToolTip("Сохранить текущие настройки как именованный профиль")
        self.btn_prof_save.clicked.connect(self._on_save_profile)
        bar.addWidget(self.btn_prof_save)

        self.btn_prof_del = QPushButton("Удалить")
        self.btn_prof_del.setToolTip("Удалить выбранный профиль")
        self.btn_prof_del.clicked.connect(self._on_delete_profile)
        bar.addWidget(self.btn_prof_del)

        self._reload_profile_list()
        return bar

    def _log(self, msg: str, ok: bool = True, sec: float = 3.5):
        clean = msg.lstrip("✓✕●○ ").strip()
        line = f"● {clean}"
        self._log_history.append(line)
        if len(self._log_history) > 10:
            self._log_history.pop(0)
        if hasattr(self, "status_lbl"):
            self._log_until = time.monotonic() + sec
            self.status_lbl.setText(line)
            self.status_lbl.setStyleSheet("color: #81c995; font-weight: 600;" if ok else "color: #f28b82; font-weight: 600;")
            self.status_lbl.setToolTip("Последние действия:\n" + "\n".join(self._log_history))

    def _update_status(self):
        ok = self.ctrl.is_connected()
        if ok and not self._was_connected:
            self._refresh_key_styles()
            if self._log_history:
                self._log("✓ Клавиатура подключена", True, 2.0)
        elif not ok and self._was_connected:
            self._log("✕ Связь с клавиатурой потеряна", False, 3.0)
        self._was_connected = ok
        if time.monotonic() < self._log_until:
            return
        t = STRINGS[self.lang]
        self.status_lbl.setText(t["status_conn"] if ok else t["status_disc"])
        self.status_lbl.setStyleSheet("color: #81c995; font-weight: 600;" if ok else "color: #f28b82; font-weight: 600;")

    def _build_keyboard_preview(self):
        self.kb_box, lay = make_card("Раскладка AK820 Max HE (клик — выбор, нажатие — тест)")
        U, GAP = 48, 5
        chassis = QFrame()
        chassis.setObjectName("chassis")
        chassis.setStyleSheet("QFrame#chassis { background-color: #101216; border: 1px solid #2a2e39; border-radius: 14px; }")
        c_lay = QVBoxLayout(chassis)
        c_lay.setContentsMargins(12, 12, 12, 12)
        c_lay.setSpacing(GAP)

        for row in ROWS:
            r_lay = QHBoxLayout()
            r_lay.setContentsMargins(0, 0, 0, 0)
            r_lay.setSpacing(GAP)
            for idx, (label, width, hid_code, slot, qt_k) in enumerate(row):
                px_w = round(width * U + (width - 1) * GAP)
                if not label:
                    spacer = QWidget()
                    spacer.setFixedSize(px_w, 38)
                    spacer.setStyleSheet("background: transparent; border: none;")
                    r_lay.addWidget(spacer)
                    continue
                btn = QPushButton(label)
                btn.setObjectName("keycap")
                btn.setFixedSize(px_w, 38)
                btn.setFocusPolicy(Qt.NoFocus)
                if slot is not None:
                    btn.clicked.connect(lambda _, s=slot, l=label: self._select_key(s, l))
                    self.key_buttons[slot] = btn
                    if qt_k is not None:
                        self.qt_key_map[qt_k] = slot
                else:
                    btn.setEnabled(False)
                r_lay.addWidget(btn)
            c_lay.addLayout(r_lay)

        row_wrap = QHBoxLayout()
        row_wrap.addStretch()
        row_wrap.addWidget(chassis)
        row_wrap.addStretch()
        lay.addLayout(row_wrap)
        return self.kb_box

    def _refresh_key_styles(self):
        adv_slots = {item[0] for item in self.adv_pair} if (self.stack.currentIndex() == 2 and self.cb_adv.currentIndex() in (1, 2)) else set()
        layer_key = "fn" if (hasattr(self, "cb_layer") and self.cb_layer.currentIndex() == 1) else "normal"
        layer_map = self.custom_map.get(layer_key, {})
        for s, b in self.key_buttons.items():
            orig_lbl, _ = self.slot_info.get(s, ("", 0))
            if s in layer_map:
                disp, tip = layer_map[s]["disp"], layer_map[s]["tip"]
                b.setText(disp)
                b.setToolTip(tip)
            else:
                b.setText(orig_lbl)
                b.setToolTip("")
            if self.is_calibrating and s in self.calibrated_slots:
                b.setStyleSheet("QPushButton#keycap { background-color: #244a32; border: 1.5px solid #81c995; color: #81c995; font-weight: 700; }")
            elif s in self.pressed_slots:
                b.setStyleSheet("QPushButton#keycap { background-color: #a8c7fa; border: 1px solid #ffffff; color: #062e6f; font-weight: 800; }")
            elif s in adv_slots or (self.stack.currentIndex() == 3 and s in layer_map and s != self.selected_slot) or (self.stack.currentIndex() == 5 and self.dks_target and s == self.dks_target):
                b.setStyleSheet("QPushButton#keycap { background-color: #3a2d19; border: 1.5px solid #ffb74d; color: #ffb74d; font-weight: 700; }")
            elif s == self.selected_slot:
                b.setStyleSheet("QPushButton#keycap { background-color: #20232c; border: 1.5px solid #a8c7fa; color: #a8c7fa; font-weight: 700; }")
            else:
                b.setStyleSheet("")

    def _resolve_slot(self, event):
        # Карта физических скан-кодов Linux (X11/Wayland) -> индекс слота матрицы
        sc_linux = {
            9: 0, 67: 1, 68: 2, 69: 3, 70: 4, 71: 5, 72: 6, 73: 7, 74: 8, 75: 9, 76: 10, 95: 11, 96: 12, 119: 106,
            49: 16, 10: 17, 11: 18, 12: 19, 13: 20, 14: 21, 15: 22, 16: 23, 17: 24, 18: 25, 19: 26, 20: 27, 21: 28, 22: 92, 110: 104,
            23: 32, 24: 33, 25: 34, 26: 35, 27: 36, 28: 37, 29: 38, 30: 39, 31: 40, 32: 41, 33: 42, 34: 43, 35: 44, 51: 60, 112: 105,
            66: 48, 38: 49, 39: 50, 40: 51, 41: 52, 42: 53, 43: 54, 44: 55, 45: 56, 46: 57, 47: 58, 48: 59, 36: 76, 117: 108,
            50: 64, 52: 65, 53: 66, 54: 67, 55: 68, 56: 69, 57: 70, 58: 71, 59: 72, 60: 73, 61: 74, 62: 75, 111: 90, 115: 107,
            37: 80, 133: 81, 64: 82, 65: 83, 108: 84, 105: 87, 113: 88, 116: 89, 114: 91
        }
        sc = event.nativeScanCode()
        if sc in sc_linux:
            return sc_linux[sc]
        return self.qt_key_map.get(event.key())

    def _pick_adv_slot(self, slot: int) -> bool:
        if self.adv_pick_idx is None:
            return False
        label, hid_c = self.slot_info.get(slot, ("", 0))
        if hid_c > 0:
            if self.adv_pick_idx == 0:
                self.adv_pair = [(slot, hid_c, label)]
                self.adv_pick_idx = 1
                self.btn_adv_pick.setText("Нажмите 2-ю...")
            else:
                self.adv_pair.append((slot, hid_c, label))
                self.adv_pick_idx = None
                self.btn_adv_pick.setChecked(False)
                self._sync_adv_pair_btns()
            self._refresh_key_styles()
        return True

    def eventFilter(self, obj, event):
        if self.is_calibrating:
            return super().eventFilter(obj, event)
        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease) and not event.isAutoRepeat():
            slot = self._resolve_slot(event)
            if slot is not None:
                is_down = (event.type() == QEvent.KeyPress)
                if self.mac_pick_mode is not None:
                    self._handle_macro_key(slot, is_down)
                    return True
                if is_down:
                    if self.adv_pick_idx is not None:
                        self._pick_adv_slot(slot)
                        return True
                    if self.cust_pick_step is not None:
                        self._pick_cust_slot(slot)
                        return True
                    if self.dks_pick_mode is not None:
                        self._pick_dks_slot(slot)
                        return True
                    self.pressed_slots.add(slot)
                else:
                    self.pressed_slots.discard(slot)
                self._refresh_key_styles()
        return super().eventFilter(obj, event)

    def _pick_cust_slot(self, slot: int) -> bool:
        if self.cust_pick_step is None:
            return False
        label, hid_c = self.slot_info.get(slot, ("", 0))
        mode_i = self.cb_ck_mode.currentIndex()
        if self.cust_pick_step == 0:
            self.cust_target = (slot, label)
            self.selected_slot = slot
            self.selected_label = label
            if mode_i == 3:
                self.cust_keys = []
                self.cust_pick_step = None
                self.btn_cust_pick.setChecked(False)
                self._sync_cust_btns()
            else:
                self.cust_pick_step = 1
                self.btn_cust_pick.setText("Нажмите Hold..." if mode_i == 1 else "Нажмите новую...")
            self._refresh_key_styles()
        elif self.cust_pick_step == 1 and hid_c > 0:
            if mode_i == 1:
                self.cust_keys = [(hid_c, label)]
                self.cust_pick_step = 2
                self.btn_cust_pick.setText("Нажмите Click...")
            else:
                self.cust_keys = [(hid_c, label), (0, "")]
                self.cust_pick_step = None
                self.btn_cust_pick.setChecked(False)
                self._sync_cust_btns()
        elif self.cust_pick_step == 2 and hid_c > 0:
            self.cust_keys.append((hid_c, label))
            self.cust_pick_step = None
            self.btn_cust_pick.setChecked(False)
            self._sync_cust_btns()
        return True

    def _handle_macro_key(self, slot: int, is_down: bool):
        label, hid_c = self.slot_info.get(slot, ("", 0))
        if self.mac_pick_mode == "target" and is_down:
            self.mac_target = (slot, label)
            self.selected_slot = slot
            self.selected_label = label
            self.mac_pick_mode = None
            self.btn_mac_target.setChecked(False)
            self.btn_mac_target.setText("Выбрать клавишу")
            self.lbl_mac_key.setText(f"Кнопка запуска: {label} (слот {slot})")
            self.lbl_mac_key.setStyleSheet("color: #ffb74d; font-weight: 600;")
            self._upd_mac_ui()
            self._refresh_key_styles()
        elif self.mac_pick_mode == "record" and hid_c > 0:
            now = time.monotonic()
            delay = 10 if self.mac_last_ts is None else max(10, min(2000, int(round((now - self.mac_last_ts) * 1000))))
            self.mac_last_ts = now
            self.macro_steps.append((hid_c, is_down, delay))
            self.lst_macro.addItem(f"{label} (0x{hid_c:02x})  |  {'Down' if is_down else 'Up'}  |  {delay} мс")
            self._upd_mac_ui()

    def _select_key(self, slot: int, label: str):
        if self.mac_pick_mode == "target":
            self._handle_macro_key(slot, True)
            return
        if self.mac_pick_mode == "record":
            self._handle_macro_key(slot, True)
            self._handle_macro_key(slot, False)
            return
        if self._pick_adv_slot(slot) or self._pick_cust_slot(slot) or self._pick_dks_slot(slot):
            return
        self.selected_slot = slot
        self.selected_label = label
        self._refresh_key_styles()
        if hasattr(self, "lbl_sel_key"):
            self.lbl_sel_key.setText(f"Выбрана клавиша: {label} (слот {slot})")
        if hasattr(self, "lbl_dks_key"):
            self.lbl_dks_key.setText(f"Клавиша для DKS: {label} (слот {slot})")

    def _footer_btn(self, text: str, callback):
        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton(text)
        btn._orig_text = text
        btn.setObjectName("primary")
        def on_click():
            callback()
            ok = self.ctrl.is_connected()
            t = STRINGS[self.lang]
            btn.setText(t["btn_written"] if ok else t["no_conn"])
            btn.setStyleSheet("background-color: #81c995; color: #062e16; font-weight: 600;" if ok else "background-color: #f28b82; color: #3c0806; font-weight: 600;")
            act = btn._orig_text.replace("Применить ", "").replace("Записать ", "").replace("Сохранить ", "").replace("Apply ", "").replace("Write ", "").replace("Save ", "").capitalize()
            self._log(t["log_ok"].format(act=act) if ok else t["log_err"], ok)
            QTimer.singleShot(1600, lambda: (btn.setText(btn._orig_text), btn.setStyleSheet("")))
        btn.clicked.connect(on_click)
        row.addWidget(btn)
        return row

    def _build_light_tab(self):
        w, lay = make_card("Настройка подсветки и анимации")

        top = QHBoxLayout()
        top.setSpacing(12)
        self.lbl_eff = QLabel("Эффект:")
        top.addWidget(self.lbl_eff)
        self.cb_effect = QComboBox()
        self.cb_effect.addItems(list(EFFECTS.keys()))
        self.cb_effect.setCurrentText("Static Brightness")
        self.cb_effect.setToolTip("Выбор режима подсветки или динамической анимации")
        top.addWidget(self.cb_effect)

        self.chk_rainbow = QCheckBox("Радужный режим (RGB)")
        self.chk_rainbow.setToolTip("Многоцветный перелив вместо фиксированного цвета")
        top.addWidget(self.chk_rainbow)

        self.cb_dir = QComboBox()
        self.cb_dir.addItems(["◀ Влево", "▶ Вправо"])
        self.cb_dir.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cb_dir.setToolTip("Направление движения волны для динамических эффектов")
        top.addWidget(self.cb_dir)

        self.btn_color = QPushButton("Выбрать цвет")
        self.btn_color.setIconSize(QSize(14, 14))
        self.btn_color.setStyleSheet("QPushButton:disabled { background-color: #181a20; border-color: #262932; color: #5f6368; }")
        self.btn_color.setToolTip("Задать статический цвет (отключается в радужном режиме)")
        self._set_color_icon(QColor(255, 0, 0))
        self.cb_effect.currentIndexChanged.connect(self._upd_light_ui)
        self.chk_rainbow.toggled.connect(self._upd_light_ui)
        self.btn_color.clicked.connect(self._pick_color)
        top.addWidget(self.btn_color)
        top.addStretch()
        lay.addLayout(top)

        knobs = QHBoxLayout()
        self.knob_bright = RotaryKnob("Яркость", 0, 5, 5, step=1, suffix=" / 5", decimals=0)
        self.knob_bright.setToolTip("Общая яркость светодиодов от 0 (выкл) до 5")
        self.knob_speed = RotaryKnob("Скорость", 1, 5, 3, step=1, suffix=" / 5", decimals=0)
        self.knob_speed.setToolTip("Скорость анимации эффектов (от 1 до 5)")
        knobs.addWidget(self.knob_bright)
        knobs.addWidget(self.knob_speed)
        knobs.addStretch()
        lay.addLayout(knobs)
        lay.addStretch()
        lay.addLayout(self._footer_btn("Применить подсветку", self._apply_light))
        self._upd_light_ui()
        return w

    def _upd_light_ui(self):
        eff = self.cb_effect.currentText()
        is_off = (eff == "Off")
        is_static = (eff == "Static Brightness")
        rb = self.chk_rainbow.isChecked()
        self.chk_rainbow.setEnabled(not is_off)
        self.btn_color.setEnabled(not is_off and not rb)
        self.cb_dir.setEnabled(not is_off and not is_static)
        self.knob_bright.setEnabled(not is_off)
        self.knob_speed.setEnabled(not is_off and not is_static)

    def _set_color_icon(self, c: QColor):
        pm = QPixmap(14, 14)
        pm.fill(Qt.transparent)
        pt = QPainter(pm)
        pt.setRenderHint(QPainter.Antialiasing)
        pt.setPen(QPen(QColor("#ffffff"), 1))
        pt.setBrush(c)
        pt.drawEllipse(1, 1, 12, 12)
        pt.end()
        self.btn_color.setIcon(QIcon(pm))

    def _pick_color(self):
        st = self.ctrl.state["light"]
        dlg = ColorPickerDialog(QColor(st["r"], st["g"], st["b"]), self, self.lang)
        if dlg.exec() == QDialog.Accepted:
            col = dlg.color
            st["r"], st["g"], st["b"] = col.red(), col.green(), col.blue()
            self._set_color_icon(col)

    def _apply_light(self):
        self.ctrl.apply_light(
            mode=EFFECTS[self.cb_effect.currentText()],
            rainbow=1 if self.chk_rainbow.isChecked() else 0,
            brightness=int(self.knob_bright.value()),
            speed=int(self.knob_speed.value()),
            direction=self.cb_dir.currentIndex()
        )

    def _build_switch_tab(self):
        w, lay = make_card("Настройка магнитных свитчей и Rapid Trigger")

        top = QHBoxLayout()
        top.setSpacing(14)
        self.lbl_ax = QLabel("Модель свитча:")
        top.addWidget(self.lbl_ax)
        self.cb_axle = QComboBox()
        self.cb_axle.addItem("Magnetic Rice Switch (4.0 мм)", 0x01)
        self.cb_axle.addItem("Magnetic Jade Pro / Magneto (3.5 мм)", 0x03)
        self.cb_axle.setToolTip("Выбор модели магнитного свитча для точного расчёта кривой датчика Холла")
        top.addWidget(self.cb_axle)

        self.chk_ft = QCheckBox("Fast Trigger (RT)")
        self.chk_ft.setChecked(True)
        self.chk_ft.setToolTip("Динамическое срабатывание и сброс клавиши при движении вниз/вверх без возврата к статической точке")
        top.addWidget(self.chk_ft)

        self.chk_full = QCheckBox("RT по всему ходу")
        self.chk_full.setToolTip("Включено: Fast Trigger работает сразу от самого верха (0.00 мм), точка срабатывания игнорируется.\nВыключено: Fast Trigger включается только после прохождения точки срабатывания.")
        top.addWidget(self.chk_full)

        top.addStretch()
        lay.addLayout(top)

        knobs = QHBoxLayout()
        self.knob_trig = RotaryKnob("Точка срабатывания", 0.10, 4.00, 1.50, step=0.05, suffix=" мм")
        self.knob_trig.setToolTip("Глубина нажатия для срабатывания (или порог активации Fast Trigger, если выключен режим по всему ходу)")
        self.knob_press = RotaryKnob("Press (нажатие)", 0.02, 2.00, 0.30, step=0.02, suffix=" мм")
        self.knob_press.setToolTip("На сколько миллиметров нужно дожать клавишу вниз для повторного срабатывания")
        self.knob_rel = RotaryKnob("Release (сброс)", 0.02, 2.00, 0.20, step=0.02, suffix=" мм")
        self.knob_rel.setToolTip("На сколько миллиметров нужно приподнять палец вверх для мгновенного отпускания клавиши")
        knobs.addWidget(self.knob_trig)
        knobs.addWidget(self.knob_press)
        knobs.addWidget(self.knob_rel)
        knobs.addStretch()
        lay.addLayout(knobs)
        lay.addStretch()
        lay.addLayout(self._footer_btn("Записать настройки свитчей", self._apply_switch))

        self.chk_ft.toggled.connect(self._update_switch_ui_state)
        self.chk_full.toggled.connect(self._update_switch_ui_state)
        self._update_switch_ui_state()
        return w

    def _toggle_pro_mode(self, on: bool):
        pairs = [
            (self.knob_trig, 0.05), (self.knob_press, 0.02), (self.knob_rel, 0.02),
            (self.knob_adv_t, 0.05), (self.knob_adv_p, 0.02), (self.knob_adv_r, 0.02),
            (self.knob_dz_t, 0.05), (self.knob_dz_b, 0.05)
        ] + [(kb, 0.10) for kb in self.dks_knobs]
        for kb, def_st in pairs:
            kb.set_step(0.01 if on else def_st)
        self._log(STRINGS[self.lang]["pro_tip"] if on else STRINGS[self.lang]["pro_off_log"], True, 3.5)

    def _update_switch_ui_state(self):
        ft = self.chk_ft.isChecked()
        full = self.chk_full.isChecked()
        self.chk_full.setEnabled(ft)
        self.knob_press.setEnabled(ft)
        self.knob_rel.setEnabled(ft)
        self.knob_trig.setEnabled(not (ft and full))

    def _apply_switch(self):
        self.ctrl.state["switch"] = {
            "axle": self.cb_axle.currentData(),
            "trigger": self.knob_trig.value(),
            "press": self.knob_press.value(),
            "release": self.knob_rel.value(),
            "ft": 1 if self.chk_ft.isChecked() else 0,
            "full": 1 if self.chk_full.isChecked() else 0
        }
        self.ctrl.apply_switches_and_adv()

    def _build_adv_tab(self):
        w, lay = make_card("Rappy Snappy и SOCD (парные функции)")

        top = QHBoxLayout()
        top.setSpacing(10)
        self.lbl_adv_m = QLabel("Режим:")
        top.addWidget(self.lbl_adv_m)
        self.cb_adv = QComboBox()
        self.cb_adv.addItems(["Отключено", "Rappy Snappy (RS)", "SOCD"])
        self.cb_adv.setToolTip("Rappy Snappy: срабатывает клавиша из пары A+D, нажатая глубже.\nSOCD: разрешение одновременного нажатия противоположных клавиш.")
        top.addWidget(self.cb_adv)

        self.lbl_socd = QLabel("Приоритет SOCD:")
        top.addWidget(self.lbl_socd)
        self.cb_socd = QComboBox()
        self.cb_socd.addItems(["Last Input", "Key 1 (A)", "Key 2 (D)", "Anti-Ghosting"])
        self.cb_socd.setCurrentIndex(3)
        self.cb_socd.setToolTip("Last Input: приоритет последнего нажатия. Key 1/2: жёсткий приоритет. Anti-Ghosting: нейтрализация.")
        top.addWidget(self.cb_socd)
        self.btn_adv_pick = QPushButton("Выбрать клавиши")
        self.btn_adv_pick.setCheckable(True)
        self.btn_adv_pick.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
        self.btn_adv_pick.setToolTip("Нажмите кнопку и по очереди нажмите две нужные клавиши на физической клавиатуре (или кликните по ним на схеме)")
        self.btn_adv_pick.clicked.connect(self._start_adv_pick)
        self.lbl_adv_pair = QLabel("Установлено: A + D")
        self.lbl_adv_pair.setStyleSheet("color: #ffb74d; font-weight: 600;")
        self.btn_adv_clear = QPushButton("Очистить")
        self.btn_adv_clear.setToolTip("Сбросить выбранную пару клавиш и отключить RS / SOCD в памяти клавиатуры")
        self.btn_adv_clear.clicked.connect(self._clear_adv_pair)
        self.adv_pair_btns = [self.btn_adv_pick, self.btn_adv_clear, self.lbl_adv_pair]
        top.addWidget(self.btn_adv_pick)
        top.addWidget(self.btn_adv_clear)
        top.addWidget(self.lbl_adv_pair)
        top.addStretch()
        lay.addLayout(top)

        knobs = QHBoxLayout()
        self.knob_adv_t = RotaryKnob("Порог срабатывания", 0.10, 4.00, 1.40, step=0.05, suffix=" мм")
        self.knob_adv_p = RotaryKnob("SOCD Press", 0.02, 2.00, 0.25, step=0.02, suffix=" мм")
        self.knob_adv_r = RotaryKnob("SOCD Release", 0.02, 2.00, 0.25, step=0.02, suffix=" мм")
        knobs.addWidget(self.knob_adv_t)
        knobs.addWidget(self.knob_adv_p)
        knobs.addWidget(self.knob_adv_r)
        knobs.addStretch()
        lay.addLayout(knobs)
        lay.addStretch()
        row_adv_f = self._footer_btn("Применить RS / SOCD", self._apply_adv)
        self.btn_adv_apply = row_adv_f.itemAt(1).widget()
        lay.addLayout(row_adv_f)
        self.cb_adv.currentIndexChanged.connect(self._upd_adv)
        self._upd_adv()
        return w

    def _start_adv_pick(self, checked: bool):
        if checked:
            self.adv_pick_idx = 0
            self.btn_adv_pick.setText("Нажмите 1-ю...")
        else:
            self.adv_pick_idx = None
            self._sync_adv_pair_btns()

    def _clear_adv_pair(self):
        self.adv_pair.clear()
        self.adv_pick_idx = None
        self.btn_adv_pick.setChecked(False)
        self.cb_adv.setCurrentIndex(0)
        self._sync_adv_pair_btns()
        self.ctrl.state["adv"]["mode"] = "none"
        self.ctrl.apply_switches_and_adv()
        self._refresh_key_styles()

    def _sync_adv_pair_btns(self):
        self.btn_adv_pick.setText("Выбрать клавиши")
        if hasattr(self, "lbl_adv_pair"):
            if len(self.adv_pair) == 2:
                p1, p2 = self.adv_pair
                self.lbl_adv_pair.setText(f"Установлено: {p1} + {p2}")
            else:
                self.lbl_adv_pair.setText("Установлено: не выбрано")

    def _upd_adv(self):
        i = self.cb_adv.currentIndex()
        self.cb_socd.setEnabled(i == 2)
        for b in self.adv_pair_btns:
            b.setEnabled(i in (1, 2))
        if hasattr(self, "lbl_adv_pair"):
            self.lbl_adv_pair.setStyleSheet("color: #ffb74d; font-weight: 600;" if i in (1, 2) else "color: #5f6368; font-weight: 600;")
        self.knob_adv_t.setEnabled(i in (1, 2))
        self.knob_adv_p.setEnabled(i == 2)
        self.knob_adv_r.setEnabled(i == 2)
        if hasattr(self, "btn_adv_apply"):
            self.btn_adv_apply.setEnabled(i == 0 or len(self.adv_pair) == 2)
        self._refresh_key_styles()

    def _apply_adv(self):
        idx = self.cb_adv.currentIndex()
        mode = "none" if idx == 0 else ("rs" if idx == 1 else "socd")
        if mode in ("rs", "socd") and len(self.adv_pair) < 2:
            return
        if len(self.adv_pair) == 2:
            (s1, h1, _), (s2, h2, _) = self.adv_pair
        else:
            s1, h1, s2, h2 = 49, 0x04, 51, 0x07
        self.ctrl.state["adv"].update({
            "mode": mode, "slot1": s1, "hid1": h1, "slot2": s2, "hid2": h2,
            "pattern": self.cb_socd.currentIndex() + 1,
            "trigger": self.knob_adv_t.value(), "press": self.knob_adv_p.value(), "release": self.knob_adv_r.value()
        })
        self.ctrl.apply_switches_and_adv()

    def _get_hid_options(self):
        return [(f"{lbl} (0x{h:02x})", h) for row in ROWS for lbl, _, h, _, _ in row if lbl and h > 0]

    def _build_custom_tab(self):
        w, lay = make_card("Переназначение клавиш, Mod-Tap и Toggle")
        row = QHBoxLayout()
        row.setSpacing(10)

        self.cb_layer = QComboBox()
        self.cb_layer.addItems(["Normal Layer", "Fn Layer"])
        self.cb_layer.setToolTip("Normal Layer: основная раскладка. Fn Layer: действие при зажатой клавише Fn")
        self.cb_layer.currentIndexChanged.connect(self._refresh_key_styles)
        row.addWidget(self.cb_layer)

        self.cb_ck_mode = QComboBox()
        self.cb_ck_mode.addItems(["Обычная клавиша", "Mod-Tap (Hold / Click)", "Toggle (Залипание)", "Сброс клавиши"])
        self.cb_ck_mode.setToolTip("Mod-Tap: разное действие при коротком клике и удержании. Toggle: залипание по клику.")
        row.addWidget(self.cb_ck_mode)

        self.btn_cust_pick = QPushButton("Выбрать клавиши")
        self.btn_cust_pick.setCheckable(True)
        self.btn_cust_pick.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
        self.btn_cust_pick.setToolTip("Нажмите и по очереди нажмите целевую клавишу и новое значение")
        self.btn_cust_pick.clicked.connect(self._start_cust_pick)
        row.addWidget(self.btn_cust_pick)

        self.btn_reset_all = QPushButton("Сбросить всё")
        self.btn_reset_all.setToolTip("Сбросить все переназначения на обоих слоях (Normal и Fn) до заводских")
        self.btn_reset_all.clicked.connect(self._reset_all_custom)
        row.addWidget(self.btn_reset_all)

        self.lbl_cust_val = QLabel("Не выбрано")
        self.lbl_cust_val.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        row.addWidget(self.lbl_cust_val)
        row.addStretch()
        lay.addLayout(row)

        self.knob_mt = RotaryKnob("Удержание MT", 50, 2000, 400, step=10, suffix=" мс", decimals=0)
        self.knob_mt.setToolTip("Время удержания в мс, после которого срабатывает действие Hold вместо Click")
        lay.addWidget(self.knob_mt, 0, Qt.AlignLeft)
        lay.addStretch()
        row_cf = self._footer_btn("Записать слой в клавиатуру", self._apply_custom)
        self.btn_cust_apply = row_cf.itemAt(1).widget()
        lay.addLayout(row_cf)
        self.cb_ck_mode.currentIndexChanged.connect(self._upd_cust)
        self._upd_cust()
        return w

    def _start_cust_pick(self, checked: bool):
        if checked:
            self.cust_pick_step = 0
            self.btn_cust_pick.setText("Нажмите целевую...")
        else:
            self.cust_pick_step = None
            self._sync_cust_btns()

    def _sync_cust_btns(self):
        mode_i = self.cb_ck_mode.currentIndex()
        self.btn_cust_pick.setText("Выбрать клавишу" if mode_i == 3 else "Выбрать клавиши")
        if hasattr(self, "btn_cust_apply"):
            ready = bool(self.cust_target) and (mode_i == 3 or len(self.cust_keys) == 2)
            self.btn_cust_apply.setEnabled(ready)
        if not self.cust_target:
            self.lbl_cust_val.setText("Не выбрано")
            self.lbl_cust_val.setStyleSheet("color: #9aa0a6; font-weight: 600;")
            return
        _, tgt_lbl = self.cust_target
        self.lbl_cust_val.setStyleSheet("color: #ffb74d; font-weight: 600;")
        if mode_i == 3:
            self.lbl_cust_val.setText(f"{tgt_lbl}  →  Сброс")
        elif len(self.cust_keys) == 2:
            (_, l1), (_, l2) = self.cust_keys
            if mode_i == 1:
                self.lbl_cust_val.setText(f"{tgt_lbl}  →  Hold: {l1} | Click: {l2}")
            else:
                prefix = "TGL " if mode_i == 2 else ""
                self.lbl_cust_val.setText(f"{tgt_lbl}  →  {prefix}{l1}")
        else:
            self.lbl_cust_val.setText(f"{tgt_lbl}  →  ...")

    def _upd_cust(self):
        i = self.cb_ck_mode.currentIndex()
        self.cust_pick_step = None
        self.btn_cust_pick.setChecked(False)
        self.knob_mt.setEnabled(i == 1)
        self._sync_cust_btns()

    def _reset_all_custom(self):
        self.custom_map["normal"].clear()
        self.custom_map["fn"].clear()
        self.cust_target = None
        self.cust_keys = []
        self.cust_pick_step = None
        self.btn_cust_pick.setChecked(False)
        self._sync_cust_btns()
        self.ctrl.apply_custom_layer("normal", {})
        self.ctrl.apply_custom_layer("fn", {})
        self._refresh_key_styles()

    def _apply_custom(self):
        if not self.cust_target:
            return
        layer = "fn" if self.cb_layer.currentIndex() == 1 else "normal"
        slot, _ = self.cust_target
        idx = self.cb_ck_mode.currentIndex()
        layer_dict = self.custom_map[layer]
        if idx == 3:
            layer_dict.pop(slot, None)
        elif len(self.cust_keys) == 2:
            (k1, l1), (k2, l2) = self.cust_keys
            if idx == 0:
                layer_dict[slot] = {"mode": "key", "k1": k1, "k2": 0, "param": 0, "disp": l1, "tip": f"Переназначено: {l1}"}
            elif idx == 1:
                ms = int(self.knob_mt.value())
                layer_dict[slot] = {"mode": "mt", "k1": k1, "k2": k2, "param": ms, "disp": f"{l1}/{l2}", "tip": f"Mod-Tap ({ms} мс): Hold {l1} | Click {l2}"}
            elif idx == 2:
                layer_dict[slot] = {"mode": "tgl", "k1": k1, "k2": 0, "param": 0, "disp": f"TGL:{l1}", "tip": f"Toggle: {l1}"}
        self.ctrl.apply_custom_layer(layer, layer_dict)
        self._refresh_key_styles()

    def _build_macro_tab(self):
        w, lay = make_card("Конструктор макросов (Shortcut Command)")
        self.macro_steps = []
        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_mac_target = QPushButton("Выбрать клавишу")
        self.btn_mac_target.setCheckable(True)
        self.btn_mac_target.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
        self.btn_mac_target.setToolTip("Нажмите и нажмите клавишу на клавиатуре, которая будет запускать макрос")
        self.btn_mac_target.clicked.connect(self._toggle_mac_target)
        row.addWidget(self.btn_mac_target)

        self.btn_mac_rec = QPushButton("Добавить клавиши")
        self.btn_mac_rec.setCheckable(True)
        self.btn_mac_rec.setStyleSheet("QPushButton:checked { background-color: #4a1c1c; border: 1.5px solid #f28b82; color: #ffffff; font-weight: 700; }")
        self.btn_mac_rec.setToolTip("Включить запись: нажимайте и отпускайте нужные клавиши на клавиатуре (или кликайте по схеме)")
        self.btn_mac_rec.clicked.connect(self._toggle_mac_rec)
        row.addWidget(self.btn_mac_rec)

        self.btn_mac_clr = QPushButton("Очистить")
        self.btn_mac_clr.setEnabled(False)
        self.btn_mac_clr.setToolTip("Очистить записанные шаги и сбросить клавишу запуска")
        self.btn_mac_clr.clicked.connect(self._clear_macro)
        row.addWidget(self.btn_mac_clr)

        self.lbl_mac_key = QLabel("Кнопка запуска: Не выбрано")
        self.lbl_mac_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        row.addWidget(self.lbl_mac_key)
        row.addStretch()
        lay.addLayout(row)

        self.lst_macro = QListWidget()
        self.lst_macro.setToolTip("Список записанных событий нажатия (Down), отпускания (Up) и задержек в миллисекундах")
        lay.addWidget(self.lst_macro)
        row_mf = self._footer_btn("Записать макрос в клавиатуру", self._save_macro)
        self.btn_mac_apply = row_mf.itemAt(1).widget()
        self.btn_mac_apply.setEnabled(False)
        lay.addLayout(row_mf)
        return w

    def _toggle_mac_target(self, checked: bool):
        self.btn_mac_rec.setChecked(False)
        self.btn_mac_rec.setText("Добавить клавиши")
        if checked:
            self.mac_pick_mode = "target"
            self.btn_mac_target.setText("Нажмите клавишу...")
        else:
            self.mac_pick_mode = None
            self.btn_mac_target.setText("Выбрать клавишу")

    def _toggle_mac_rec(self, checked: bool):
        self.btn_mac_target.setChecked(False)
        self.btn_mac_target.setText("Выбрать клавишу")
        if checked:
            self.mac_pick_mode = "record"
            self.mac_last_ts = None
            self.btn_mac_rec.setText("● Идёт запись... (Стоп)")
        else:
            self.mac_pick_mode = None
            self.btn_mac_rec.setText("Добавить клавиши")

    def _clear_macro(self):
        self.mac_pick_mode = None
        self.mac_target = None
        self.mac_last_ts = None
        self.btn_mac_target.setChecked(False)
        self.btn_mac_rec.setChecked(False)
        self.btn_mac_target.setText("Выбрать клавишу")
        self.btn_mac_rec.setText("Добавить клавиши")
        self.lbl_mac_key.setText("Кнопка запуска: Не выбрано")
        self.lbl_mac_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        self.macro_steps.clear()
        self.lst_macro.clear()
        self._upd_mac_ui()

    def _upd_mac_ui(self):
        if hasattr(self, "btn_mac_apply"):
            self.btn_mac_apply.setEnabled(bool(self.mac_target) and len(self.macro_steps) > 0)
            self.btn_mac_clr.setEnabled(bool(self.mac_target) or len(self.macro_steps) > 0)

    def _save_macro(self):
        if self.mac_target and self.macro_steps:
            slot, _ = self.mac_target
            self.ctrl.apply_macro(slot, self.macro_steps)

    def _pick_dks_slot(self, slot: int) -> bool:
        if self.dks_pick_mode is None:
            return False
        label, hid_c = self.slot_info.get(slot, ("", 0))
        if self.dks_pick_mode == "target":
            self.dks_target = (slot, label)
            self.selected_slot = slot
            self.selected_label = label
            self.dks_pick_mode = None
            self.btn_dks_target.setChecked(False)
            self.btn_dks_target.setText("Выбрать клавишу")
            self.lbl_dks_key.setText(f"Клавиша DKS: {label} (слот {slot})")
            self.lbl_dks_key.setStyleSheet("color: #ffb74d; font-weight: 600;")
            self._upd_dks_ui()
            self._refresh_key_styles()
        elif isinstance(self.dks_pick_mode, int) and hid_c > 0:
            idx = self.dks_pick_mode
            old_list = list(self.dks_keys)
            old_list.pop(idx)
            old_list.insert(idx, (hid_c, label))
            self.dks_keys = old_list
            self._sync_dks_btns()
            if self.btn_dks_add.isChecked() and idx < 3:
                self.dks_pick_mode = idx + 1
                self.btn_dks_add.setText(f"Нажмите точку {idx + 2}...")
            else:
                self.dks_pick_mode = None
                self.btn_dks_add.setChecked(False)
                self.btn_dks_add.setText("Добавить клавиши")
        return True

    def _build_dks_tab(self):
        w, lay = make_card("DKS — Dynamic Key Stroke (4 уровня хода одной клавиши)")
        top = QHBoxLayout()
        top.setSpacing(10)

        self.btn_dks_target = QPushButton("Выбрать клавишу")
        self.btn_dks_target.setCheckable(True)
        self.btn_dks_target.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
        self.btn_dks_target.setToolTip("Нажмите и нажмите на клавиатуре клавишу, для которой настраивается DKS")
        self.btn_dks_target.clicked.connect(self._toggle_dks_target)
        top.addWidget(self.btn_dks_target)

        self.btn_dks_add = QPushButton("Добавить клавиши")
        self.btn_dks_add.setCheckable(True)
        self.btn_dks_add.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
        self.btn_dks_add.setToolTip("Поочерёдно назначить до 4 клавиш на точки хода 1..4 нажатием на клавиатуре")
        self.btn_dks_add.clicked.connect(self._toggle_dks_add)
        top.addWidget(self.btn_dks_add)

        self.btn_dks_clr = QPushButton("Очистить")
        self.btn_dks_clr.setEnabled(False)
        self.btn_dks_clr.setToolTip("Сбросить целевую клавишу и все 4 точки DKS")
        self.btn_dks_clr.clicked.connect(self._clear_dks)
        top.addWidget(self.btn_dks_clr)

        self.lbl_dks_key = QLabel("Клавиша DKS: Не выбрано")
        self.lbl_dks_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        top.addWidget(self.lbl_dks_key)
        top.addStretch()
        lay.addLayout(top)

        grid = QHBoxLayout()
        grid.setSpacing(14)
        self.dks_knobs, self.dks_btns = [], []
        for idx, d_val in enumerate([0.8, 1.6, 2.4, 3.2]):
            col = QVBoxLayout()
            kb = RotaryKnob(f"Точка {idx+1}", 0.1, 4.0, d_val, step=0.1, suffix=" мм", decimals=1)
            kb.setToolTip(f"Глубина нажатия (в мм) для срабатывания {idx+1}-й точки DKS")
            btn = QPushButton(f"Точка {idx+1}: —")
            btn.setCheckable(True)
            btn.setStyleSheet("QPushButton:checked { background-color: #004a77; border: 1.5px solid #a8c7fa; color: #ffffff; font-weight: 700; }")
            btn.setToolTip("Нажмите и нажмите нужную клавишу на клавиатуре для этой точки хода")
            btn.clicked.connect(lambda chk, i=idx: self._toggle_dks_point(i, chk))
            col.addWidget(kb)
            col.addWidget(btn)
            grid.addLayout(col)
            self.dks_knobs.append(kb)
            self.dks_btns.append(btn)
        grid.addStretch()
        lay.addLayout(grid)
        lay.addStretch()
        row_df = self._footer_btn("Записать DKS в клавиатуру", self._apply_dks)
        self.btn_dks_apply = row_df.itemAt(1).widget()
        lay.addLayout(row_df)
        self._upd_dks_ui()
        return w

    def _toggle_dks_target(self, checked: bool):
        self.btn_dks_add.setChecked(False)
        self.btn_dks_add.setText("Добавить клавиши")
        for b in self.dks_btns: b.setChecked(False)
        if checked:
            self.dks_pick_mode = "target"
            self.btn_dks_target.setText("Нажмите клавишу...")
        else:
            self.dks_pick_mode = None
            self.btn_dks_target.setText("Выбрать клавишу")

    def _toggle_dks_add(self, checked: bool):
        self.btn_dks_target.setChecked(False)
        self.btn_dks_target.setText("Выбрать клавишу")
        for b in self.dks_btns: b.setChecked(False)
        if checked:
            self.dks_pick_mode = 0
            self.btn_dks_add.setText("Нажмите точку 1...")
        else:
            self.dks_pick_mode = None
            self.btn_dks_add.setText("Добавить клавиши")

    def _toggle_dks_point(self, idx: int, checked: bool):
        self.btn_dks_target.setChecked(False)
        self.btn_dks_target.setText("Выбрать клавишу")
        self.btn_dks_add.setChecked(False)
        self.btn_dks_add.setText("Добавить клавиши")
        for i, b in enumerate(self.dks_btns):
            b.setChecked(checked and i == idx)
        self.dks_pick_mode = idx if checked else None
        self._sync_dks_btns()

    def _sync_dks_btns(self):
        for idx, (btn, (_, lbl)) in enumerate(zip(self.dks_btns, self.dks_keys)):
            btn.setChecked(self.dks_pick_mode == idx)
            btn.setText("Нажмите..." if self.dks_pick_mode == idx else f"Точка {idx+1}: {lbl}")

    def _clear_dks(self):
        if self.dks_target:
            slot, _ = self.dks_target
            self.ctrl.apply_dks(slot, False, [0.8, 1.6, 2.4, 3.2], list(bytes(4)), list(bytes(4)))
        self.btn_dks_target.setChecked(False)
        self.btn_dks_add.setChecked(False)
        self.btn_dks_target.setText("Выбрать клавишу")
        self.btn_dks_add.setText("Добавить клавиши")
        self.lbl_dks_key.setText("Клавиша DKS: Не выбрано")
        self.lbl_dks_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        self._sync_dks_btns()
        self._upd_dks_ui()
        self._refresh_key_styles()

    def _upd_dks_ui(self):
        has_t = bool(self.dks_target)
        self.btn_dks_add.setEnabled(has_t)
        if hasattr(self, "btn_dks_clr"):
            self.btn_dks_clr.setEnabled(has_t)
        for kb, b in zip(self.dks_knobs, self.dks_btns):
            kb.setEnabled(has_t)
            b.setEnabled(has_t)
        if hasattr(self, "btn_dks_apply"):
            self.btn_dks_apply.setEnabled(has_t)

    def _apply_dks(self):
        if not self.dks_target:
            return
        slot, _ = self.dks_target
        keys = [k for k, _ in self.dks_keys]
        en = any(k > 0 for k in keys)
        self.ctrl.apply_dks(slot, en, [kb.value() for kb in self.dks_knobs], keys, [0x01 if k > 0 else 0x00 for k in keys])

    def _build_calib_tab(self):
        w, lay = make_card("Системные параметры, Dead Zone и калибровка")
        top = QHBoxLayout()
        top.addWidget(QLabel("Polling Rate:"))
        self.cb_rate = QComboBox()
        self.cb_rate.addItems(["1000 Гц (1K)", "4000 Гц (4K)", "8000 Гц (8K)"])
        self.cb_rate.setCurrentIndex(2)
        self.chk_stab = QCheckBox("Stability Mode"); self.chk_stab.setChecked(True)
        self.chk_adap = QCheckBox("Adaptive Calibration"); self.chk_adap.setChecked(True)
        self.chk_dz = QCheckBox("Dead Zone"); self.chk_dz.setChecked(True)
        for item in (self.cb_rate, self.chk_stab, self.chk_adap, self.chk_dz): top.addWidget(item)
        top.addStretch(); lay.addLayout(top)
        knobs = QHBoxLayout()
        self.knob_dz_t = RotaryKnob("Top Dead Zone", 0.00, 1.00, 0.30, step=0.05, suffix=" мм")
        self.knob_dz_b = RotaryKnob("Bottom Dead Zone", 0.00, 1.00, 0.30, step=0.05, suffix=" мм")
        knobs.addWidget(self.knob_dz_t); knobs.addWidget(self.knob_dz_b); knobs.addStretch()
        lay.addLayout(knobs)
        self.chk_dz.toggled.connect(lambda dz: (self.knob_dz_t.setEnabled(dz), self.knob_dz_b.setEnabled(dz)))
        cal_row = QHBoxLayout()
        self.btn_cal_start = QPushButton("Старт калибровки"); self.btn_cal_start.clicked.connect(self._cal_start)
        self.btn_cal_clear = QPushButton("Сброс (Clear)"); self.btn_cal_clear.setEnabled(False); self.btn_cal_clear.clicked.connect(self._cal_clear)
        self.btn_cal_save = QPushButton("Применить (Save)"); self.btn_cal_save.setObjectName("primary"); self.btn_cal_save.setEnabled(False); self.btn_cal_save.clicked.connect(self._cal_save)
        self.lbl_cal = QLabel("Нажмите «Старт» и прожмите нужные клавиши до упора.")
        for item in (self.btn_cal_start, self.btn_cal_clear, self.btn_cal_save, self.lbl_cal): cal_row.addWidget(item)
        cal_row.addStretch(); lay.addLayout(cal_row); lay.addStretch()
        row_sys = self._footer_btn("Сохранить системные настройки", self._apply_sys)
        self.btn_rst = QPushButton("Общий сброс")
        self.btn_rst.setStyleSheet("QPushButton { background-color: #3b1d1e; border: 1px solid #f28b82; color: #f28b82; font-weight: 600; border-radius: 18px; padding: 9px 20px; } QPushButton:hover { background-color: #4f2527; }")
        self.btn_rst.setToolTip("Сбросить все настройки клавиатуры (подсветку, свитчи, RS/SOCD, раскладку, DKS и систему) к заводским")
        self.btn_rst.clicked.connect(self._on_factory_reset)
        row_sys.insertWidget(0, self.btn_rst)
        lay.addLayout(row_sys)
        return w

    def _set_lang(self, lang: str, save: bool = True):
        self.lang = lang if lang in STRINGS else "ru"
        self.btn_ru.setChecked(self.lang == "ru")
        self.btn_en.setChecked(self.lang == "en")
        t = STRINGS[self.lang]
        for i, b in enumerate(self.nav_buttons):
            b.setText(t[f"nav_{i}"])
        self.chk_pro.setText(t["pro_chk"])
        self.chk_pro.setToolTip(t["pro_tip"])
        self.lbl_prof.setText(t["prof_lbl"])
        self.btn_prof_load.setText(t["prof_load"])
        self.btn_prof_save.setText(t["prof_save"])
        self.btn_prof_del.setText(t["prof_del"])
        if hasattr(self.kb_box, "_title_lbl"): self.kb_box._title_lbl.setText(t["kb_title"])
        cards = [self.stack.widget(i) for i in range(7)]
        c_keys = ["card_light", "card_sw", "card_adv", "card_cust", "card_mac", "card_dks", "card_sys"]
        for cw, ck in zip(cards, c_keys):
            if hasattr(cw, "_title_lbl"):
                cw._title_lbl.setText(t[ck])
        self.lbl_eff.setText(t["lbl_effect"])
        self.chk_rainbow.setText(t["chk_rainbow"])
        self.cb_dir.setItemText(0, t["dir_l"])
        self.cb_dir.setItemText(1, t["dir_r"])
        self.btn_color.setText(t["btn_color"])
        self.knob_bright.lbl_t.setText(t["knob_bright"])
        self.knob_speed.lbl_t.setText(t["knob_speed"])
        self.lbl_ax.setText(t["lbl_axle"])
        self.chk_ft.setText(t["chk_ft"])
        self.chk_full.setText(t["chk_full"])
        self.knob_trig.lbl_t.setText(t["knob_trig"])
        self.knob_press.lbl_t.setText(t["knob_press"])
        self.knob_rel.lbl_t.setText(t["knob_rel"])
        self.knob_adv_t.lbl_t.setText(t["knob_trig"])
        self.knob_adv_p.lbl_t.setText(t["knob_press"])
        self.knob_adv_r.lbl_t.setText(t["knob_rel"])
        self.knob_mt.lbl_t.setText(t["knob_mt"])
        self.btn_mac_target.setText(t["btn_pick_key"])
        self.btn_mac_rec.setText(t["btn_add_keys"])
        self.btn_mac_clr.setText(t["btn_clear"])
        self.btn_dks_target.setText(t["btn_pick_key"])
        self.btn_dks_add.setText(t["btn_add_keys"])
        self.btn_dks_clr.setText(t["btn_clear"])
        self.btn_cal_start.setText(t["btn_cal_start"])
        self.btn_cal_clear.setText(t["btn_cal_clear"])
        self.btn_cal_save.setText(t["btn_cal_save"])
        self.btn_rst.setText(t["btn_factory"])
        for i, b in enumerate(self.nav_buttons):
            b.setToolTip(t[f"tip_{i}"])
        self.lbl_adv_m.setText(t["lbl_mode"])
        self.lbl_socd.setText(t["lbl_socd"])
        self.cb_adv.setItemText(0, t["adv_off"])
        self.btn_adv_pick.setText(t["btn_pick_pair"])
        self.btn_adv_clear.setText(t["btn_clear"])
        if not self.adv_pair:
            self.lbl_adv_pair.setText(t["pair_none"])
        for idx_m in range(4):
            self.cb_ck_mode.setItemText(idx_m, t[f"ck_m{idx_m}"])
        self.btn_cust_pick.setText(t["btn_pick_key"] if self.cb_ck_mode.currentIndex() == 3 else t["btn_pick_pair"])
        self.btn_reset_all.setText(t["btn_reset_all"])
        if not self.cust_target:
            self.lbl_cust_val.setText("Не выбрано" if self.lang == "ru" else "Not selected")
        if not self.mac_target:
            self.lbl_mac_key.setText(t["mac_none"])
        if not self.dks_target:
            self.lbl_dks_key.setText(t["dks_none"])
        for idx_d, (btn_d, (_, lbl_d)) in enumerate(zip(self.dks_btns, self.dks_keys)):
            btn_d.setText(f"{t['dks_pt']} {idx_d+1}: {lbl_d}")
        for idx_r in range(3):
            self.cb_rate.setItemText(idx_r, t[f"rate_{idx_r}"])
        if not self.is_calibrating:
            self.lbl_cal.setText(t["cal_hint"])
        f_keys = ["btn_apply_light", "btn_apply_sw", "btn_apply_adv", "btn_apply_cust", "btn_apply_mac", "btn_apply_dks", "btn_apply_sys"]
        for cw, fk in zip(cards, f_keys):
            for b in cw.findChildren(QPushButton):
                if b.objectName() == "primary":
                    b._orig_text = t[fk]
                    b.setText(t[fk])
        self.btn_ru.setToolTip(t["tt_ru"])
        self.btn_en.setToolTip(t["tt_en"])
        self.btn_prof_load.setToolTip(t["tt_pload"])
        self.btn_prof_save.setToolTip(t["tt_psave"])
        self.btn_prof_del.setToolTip(t["tt_pdel"])
        self.cb_effect.setToolTip(t["tt_eff"])
        self.chk_rainbow.setToolTip(t["tt_rb"])
        self.cb_dir.setToolTip(t["tt_dir"])
        self.btn_color.setToolTip(t["tt_col"])
        self.knob_bright.setToolTip(t["tt_bright"])
        self.knob_speed.setToolTip(t["tt_speed"])
        self.cb_axle.setToolTip(t["tt_axle"])
        self.chk_ft.setToolTip(t["tt_ft"])
        self.chk_full.setToolTip(t["tt_full"])
        self.knob_trig.setToolTip(t["tt_trig"])
        self.knob_press.setToolTip(t["tt_press"])
        self.knob_rel.setToolTip(t["tt_rel"])
        self.cb_adv.setToolTip(t["tt_adv_m"])
        self.cb_socd.setToolTip(t["tt_socd"])
        self.btn_adv_pick.setToolTip(t["tt_adv_p"])
        self.btn_adv_clear.setToolTip(t["tt_adv_c"])
        self.knob_adv_t.setToolTip(t["tt_trig"])
        self.knob_adv_p.setToolTip(t["tt_press"])
        self.knob_adv_r.setToolTip(t["tt_rel"])
        self.cb_layer.setToolTip(t["tt_layer"])
        self.cb_ck_mode.setToolTip(t["tt_ck_m"])
        self.btn_cust_pick.setToolTip(t["tt_ck_p"])
        self.btn_reset_all.setToolTip(t["tt_ck_r"])
        self.knob_mt.setToolTip(t["tt_mt"])
        self.btn_mac_target.setToolTip(t["tt_mac_t"])
        self.btn_mac_rec.setToolTip(t["tt_mac_r"])
        self.btn_mac_clr.setToolTip(t["tt_mac_c"])
        self.btn_dks_target.setToolTip(t["tt_dks_t"])
        self.btn_dks_add.setToolTip(t["tt_dks_a"])
        self.btn_dks_clr.setToolTip(t["tt_dks_c"])
        for kb_d in self.dks_knobs:
            kb_d.setToolTip(t["tt_dks_k"])
        self.cb_rate.setToolTip(t["tt_rate"])
        self.chk_stab.setToolTip(t["tt_stab"])
        self.chk_adap.setToolTip(t["tt_adap"])
        self.chk_dz.setToolTip(t["tt_dz"])
        self.knob_dz_t.setToolTip(t["tt_dzt"])
        self.knob_dz_b.setToolTip(t["tt_dzb"])
        self.btn_cal_start.setToolTip(t["tt_cal_s"])
        self.btn_cal_clear.setToolTip(t["tt_cal_c"])
        self.btn_cal_save.setToolTip(t["tt_cal_v"])
        self.btn_rst.setToolTip(t["tt_rst"])
        self._update_status()
        if save:
            self._persist_ui_state()

    def _ask(self, title: str, text: str) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.NoIcon)
        btn_yes = box.addButton(STRINGS[self.lang]["yes"], QMessageBox.YesRole)
        btn_yes.setObjectName("primary")
        btn_no = box.addButton(STRINGS[self.lang]["no"], QMessageBox.NoRole)
        box.setDefaultButton(btn_no)
        box.exec()
        return box.clickedButton() == btn_yes

    def _on_factory_reset(self):
        if not self._ask(STRINGS[self.lang]["rst_title"], STRINGS[self.lang]["rst_q"]):
            return
        self.ctrl.factory_reset()
        self.cb_effect.setCurrentText("Spectrum Cycle")
        self.chk_rainbow.setChecked(True)
        self.cb_dir.setCurrentIndex(0)
        self._set_color_icon(QColor(255, 0, 0))
        self.knob_bright.setValue(5)
        self.knob_speed.setValue(3)
        self.cb_axle.setCurrentIndex(0)
        self.chk_ft.setChecked(False)
        self.chk_full.setChecked(False)
        self.chk_pro.setChecked(False)
        self.knob_trig.setValue(1.50)
        self.knob_press.setValue(0.30)
        self.knob_rel.setValue(0.20)
        self.adv_pair.clear()
        self.adv_pick_idx = None
        self.btn_adv_pick.setChecked(False)
        self.cb_adv.setCurrentIndex(0)
        self._sync_adv_pair_btns()
        self.custom_map["normal"].clear()
        self.custom_map["fn"].clear()
        self.cust_target = None
        self.cust_keys = []
        self.cust_pick_step = None
        self.btn_cust_pick.setChecked(False)
        self._sync_cust_btns()
        self._clear_macro()
        self.dks_pick_mode = None
        self.dks_target = None
        self.dks_keys = [(0, "—"), (0, "—"), (0, "—"), (0, "—")]
        for kb, d_val in zip(self.dks_knobs, [0.8, 1.6, 2.4, 3.2]):
            kb.setValue(d_val)
        self.btn_dks_target.setChecked(False)
        self.btn_dks_add.setChecked(False)
        self.btn_dks_target.setText("Выбрать клавишу")
        self.btn_dks_add.setText("Добавить клавиши")
        self.lbl_dks_key.setText("Клавиша DKS: Не выбрано")
        self.lbl_dks_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        self._sync_dks_btns()
        self._upd_dks_ui()
        self.cb_rate.setCurrentIndex(2)
        self.chk_stab.setChecked(True)
        self.chk_adap.setChecked(True)
        self.chk_dz.setChecked(True)
        self.knob_dz_t.setValue(0.30)
        self.knob_dz_b.setValue(0.30)
        self._refresh_key_styles()
        self.ctrl.clear_last_state()
        self._log(STRINGS[self.lang]["log_rst"], True, 4.0)

    def _apply_sys(self):
        self.ctrl.apply_settings(rate=[0x03, 0x05, 0x06][self.cb_rate.currentIndex()], stability=int(self.chk_stab.isChecked()), adaptive=int(self.chk_adap.isChecked()), dz_enable=int(self.chk_dz.isChecked()), dz_top=self.knob_dz_t.value(), dz_bottom=self.knob_dz_b.value())

    def _cal_start(self):
        if not self.ctrl.start_calibration(clear=True): return
        self.ctrl.open_telemetry(); self.calibrated_slots.clear(); self.is_calibrating = True
        self.btn_cal_start.setEnabled(False); self.btn_cal_clear.setEnabled(True); self.btn_cal_save.setEnabled(True)
        self._refresh_key_styles(); self._tick_calib()

    def _cal_clear(self):
        self.ctrl.send_packets([[0xaa, 0x0f, 0x05]], delay=0.1); self.calibrated_slots.clear(); self._refresh_key_styles()
        self.lbl_cal.setText("Данные очищены. Прожмите клавиши до упора.")

    def _cal_save(self):
        self.is_calibrating = False
        self._was_connected = False
        self.lang = 'ru'
        self._prof_done.connect(self._on_prof_written)
        self._log_until = 0.0
        self._log_history = []; self.ctrl.close_telemetry(); self.ctrl.finish_calibration(); self._refresh_key_styles()
        self.btn_cal_start.setEnabled(True); self.btn_cal_clear.setEnabled(False); self.btn_cal_save.setEnabled(False)
        self.lbl_cal.setText(f"Калибровка сохранена! Откалибровано клавиш: {len(self.calibrated_slots)}")

    def _tick_calib(self):
        if not self.is_calibrating: return
        new_slots = self.ctrl.poll_calibration_slots()
        if new_slots - self.calibrated_slots: self.calibrated_slots.update(new_slots); self._refresh_key_styles()
        self.lbl_cal.setText(f"Калибровка активна — прожато клавиш: {len(self.calibrated_slots)}")
        QTimer.singleShot(25, self._tick_calib)

    def _sync_state_from_widgets(self):
        st = self.ctrl.state
        st["light"].update({
            "mode": EFFECTS[self.cb_effect.currentText()],
            "rainbow": 1 if self.chk_rainbow.isChecked() else 0,
            "direction": 1 if self.cb_dir.currentIndex() == 1 else 0,
            "brightness": int(self.knob_bright.value()),
            "speed": int(self.knob_speed.value())
        })
        st["switch"].update({
            "axle": 0x03 if self.cb_axle.currentIndex() == 1 else 0x01,
            "ft": 1 if self.chk_ft.isChecked() else 0,
            "full": 1 if self.chk_full.isChecked() else 0,
            "trigger": round(self.knob_trig.value(), 2),
            "press": round(self.knob_press.value(), 2),
            "release": round(self.knob_rel.value(), 2)
        })
        idx_a = self.cb_adv.currentIndex()
        mode_a = "none" if idx_a == 0 else ("rs" if idx_a == 1 else "socd")
        s1, h1 = (self.adv_pair[0][0], self.adv_pair[0][1]) if len(self.adv_pair) == 2 else (49, 0x04)
        s2, h2 = (self.adv_pair[1][0], self.adv_pair[1][1]) if len(self.adv_pair) == 2 else (51, 0x07)
        st["adv"].update({
            "mode": mode_a, "slot1": s1, "hid1": h1, "slot2": s2, "hid2": h2,
            "pattern": self.cb_socd.currentIndex() + 1,
            "trigger": round(self.knob_adv_t.value(), 2),
            "press": round(self.knob_adv_p.value(), 2),
            "release": round(self.knob_adv_r.value(), 2)
        })
        st["settings"].update({
            "rate": [0x03, 0x05, 0x06][self.cb_rate.currentIndex()],
            "stability": int(self.chk_stab.isChecked()),
            "adaptive": int(self.chk_adap.isChecked()),
            "dz_enable": int(self.chk_dz.isChecked()),
            "dz_top": round(self.knob_dz_t.value(), 2),
            "dz_bottom": round(self.knob_dz_b.value(), 2)
        })

    def _persist_ui_state(self):
        self._sync_state_from_widgets()
        extra = {
            "lang": self.lang,
            "adv_pair": self.adv_pair,
            "custom_map": {
                "normal": {str(k): v for k, v in self.custom_map["normal"].items()},
                "fn": {str(k): v for k, v in self.custom_map["fn"].items()}
            },
            "macro": {"target": self.mac_target, "steps": self.macro_steps},
            "dks": {
                "target": self.dks_target,
                "keys": self.dks_keys,
                "depths": [round(kb.value(), 1) for kb in self.dks_knobs]
            }
        }
        self.ctrl.save_last_state(extra)

    def _restore_ui_state(self):
        extra = self.ctrl.load_last_state()
        if extra.get("lang") in ("ru", "en"):
            self._set_lang(extra["lang"], save=False)
        st = self.ctrl.state
        lt = st.get("light", {})
        inv_eff = {v: k for k, v in EFFECTS.items()}
        if lt.get("mode") in inv_eff:
            self.cb_effect.setCurrentText(inv_eff[lt["mode"]])
        self.chk_rainbow.setChecked(bool(lt.get("rainbow", 0)))
        self.cb_dir.setCurrentIndex(1 if lt.get("direction", 0) else 0)
        self._set_color_icon(QColor(lt.get("r", 255), lt.get("g", 0), lt.get("b", 0)))
        self.knob_bright.setValue(lt.get("brightness", 5))
        self.knob_speed.setValue(lt.get("speed", 3))
        self._upd_light_ui()

        sw = st.get("switch", {})
        self.cb_axle.setCurrentIndex(1 if sw.get("axle") == 0x03 else 0)
        self.chk_ft.setChecked(bool(sw.get("ft", 0)))
        self.chk_full.setChecked(bool(sw.get("full", 0)))
        self.knob_trig.setValue(sw.get("trigger", 1.50))
        self.knob_press.setValue(sw.get("press", 0.30))
        self.knob_rel.setValue(sw.get("release", 0.20))

        adv = st.get("adv", {})
        m = adv.get("mode", "none")
        self.cb_adv.setCurrentIndex(0 if m == "none" else (1 if m == "rs" else 2))
        self.cb_socd.setCurrentIndex(max(0, min(3, adv.get("pattern", 4) - 1)))
        self.knob_adv_t.setValue(adv.get("trigger", 1.40))
        self.knob_adv_p.setValue(adv.get("press", 0.25))
        self.knob_adv_r.setValue(adv.get("release", 0.25))
        if "adv_pair" in extra and len(extra["adv_pair"]) == 2:
            self.adv_pair = [tuple(x) for x in extra["adv_pair"]]
        else:
            self.adv_pair.clear()
        self._sync_adv_pair_btns()
        self._upd_adv()

        cmap = extra.get("custom_map", {})
        for lyr in ("normal", "fn"):
            self.custom_map[lyr] = {int(k): v for k, v in cmap.get(lyr, {}).items()}

        mac = extra.get("macro", {})
        self.mac_target = tuple(mac["target"]) if mac.get("target") else None
        self.macro_steps = [tuple(x) for x in mac.get("steps", [])]
        self.lst_macro.clear()
        inv_hid = {h: lbl for lbl, h in self.slot_info.values() if h > 0}
        for code, is_down, delay in self.macro_steps:
            lbl = inv_hid.get(code, f"0x{code:02x}")
            self.lst_macro.addItem(f"{lbl} (0x{code:02x})  |  {'Down' if is_down else 'Up'}  |  {delay} мс")
        if self.mac_target:
            self.lbl_mac_key.setText(f"Кнопка запуска: {self.mac_target[1]} (слот {self.mac_target[0]})")
            self.lbl_mac_key.setStyleSheet("color: #ffb74d; font-weight: 600;")
        else:
            self.lbl_mac_key.setText("Кнопка запуска: Не выбрано")
            self.lbl_mac_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        self._upd_mac_ui()

        dks = extra.get("dks", {})
        self.dks_target = tuple(dks["target"]) if dks.get("target") else None
        self.dks_keys = [tuple(x) for x in dks.get("keys", [(0, "—"), (0, "—"), (0, "—"), (0, "—")])]
        for kb, val in zip(self.dks_knobs, dks.get("depths", [0.8, 1.6, 2.4, 3.2])):
            kb.setValue(val)
        if self.dks_target:
            self.lbl_dks_key.setText(f"Клавиша DKS: {self.dks_target[1]} (слот {self.dks_target[0]})")
            self.lbl_dks_key.setStyleSheet("color: #ffb74d; font-weight: 600;")
        else:
            self.lbl_dks_key.setText("Клавиша DKS: Не выбрано")
            self.lbl_dks_key.setStyleSheet("color: #9aa0a6; font-weight: 600;")
        self._sync_dks_btns()
        self._upd_dks_ui()

        cfg = st.get("settings", {})
        r_map = {0x03: 0, 0x05: 1, 0x06: 2}
        self.cb_rate.setCurrentIndex(r_map.get(cfg.get("rate", 0x06), 2))
        self.chk_stab.setChecked(bool(cfg.get("stability", 1)))
        self.chk_adap.setChecked(bool(cfg.get("adaptive", 1)))
        self.chk_dz.setChecked(bool(cfg.get("dz_enable", 1)))
        self.knob_dz_t.setValue(cfg.get("dz_top", 0.30))
        self.knob_dz_b.setValue(cfg.get("dz_bottom", 0.30))
        self._refresh_key_styles()

    def _profiles_dir(self):
        d = os.path.expanduser("~/.config/ajazz_studio/profiles")
        os.makedirs(d, exist_ok=True)
        return d

    def _reload_profile_list(self, select_name: str = None):
        cur = select_name or self.cb_profiles.currentText()
        self.cb_profiles.clear()
        d = self._profiles_dir()
        names = sorted(os.path.splitext(fn)[0] for fn in os.listdir(d) if fn.endswith(".json"))
        for n in names:
            self.cb_profiles.addItem(n)
        has_p = len(names) > 0
        self.cb_profiles.setEnabled(has_p)
        self.btn_prof_load.setEnabled(has_p)
        self.btn_prof_del.setEnabled(has_p)
        if cur and cur in names:
            self.cb_profiles.setCurrentText(cur)

    def _on_save_profile(self):
        cur = self.cb_profiles.currentText() or STRINGS[self.lang]["def_prof"]
        dlg = QInputDialog(self)
        dlg.setWindowTitle(STRINGS[self.lang]["save_title"])
        dlg.setLabelText(STRINGS[self.lang]["save_lbl"])
        dlg.setTextValue(cur)
        dlg.setOkButtonText(STRINGS[self.lang]["save_btn"])
        dlg.setCancelButtonText(STRINGS[self.lang]["cancel_btn"])
        ok = (dlg.exec() == QDialog.Accepted)
        name = dlg.textValue()
        name = name.strip()
        if not ok or not name:
            return
        safe = "".join(c for c in name if c not in '/\\:*?"<>|').strip()
        if not safe:
            return
        self._persist_ui_state()
        src = self.ctrl._state_path()
        dst = os.path.join(self._profiles_dir(), f"{safe}.json")
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8") as f:
                data = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(data)
        self._reload_profile_list(select_name=safe)
        self._log(STRINGS[self.lang]["log_psave"].format(name=safe), True)

    def _on_load_profile(self):
        name = self.cb_profiles.currentText()
        if not name:
            return
        path = os.path.join(self._profiles_dir(), f"{name}.json")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        with open(self.ctrl._state_path(), "w", encoding="utf-8") as f:
            f.write(raw)
        self._restore_ui_state()
        if not self.ctrl.is_connected():
            self._on_prof_written(name, False)
            return
        self.btn_prof_load.setEnabled(False)
        self.btn_prof_load.setText(STRINGS[self.lang]["prof_writing"])
        c_norm = dict(self.custom_map["normal"])
        c_fn = dict(self.custom_map["fn"])
        mac_t, mac_s = self.mac_target, list(self.macro_steps)
        dks_t = self.dks_target
        dks_d = [kb.value() for kb in self.dks_knobs]
        dks_k = [k for k, _ in self.dks_keys]
        def worker():
            try:
                ok = self.ctrl.apply_light()
                self.ctrl.apply_settings()
                self.ctrl.apply_switches_and_adv()
                self.ctrl.apply_custom_layer("normal", c_norm)
                self.ctrl.apply_custom_layer("fn", c_fn)
                if mac_t and mac_s:
                    self.ctrl.apply_macro(mac_t, mac_s)
                if dks_t:
                    en = any(k > 0 for k in dks_k)
                    self.ctrl.apply_dks(dks_t, en, dks_d, dks_k, [0x01 if k > 0 else 0x00 for k in dks_k])
            except Exception:
                ok = False
            self._prof_done.emit(name, ok)
        threading.Thread(target=worker, daemon=True).start()

    def _on_prof_written(self, name: str, ok: bool):
        self.btn_prof_load.setEnabled(True)
        self.btn_prof_load.setText(STRINGS[self.lang]["prof_loaded"] if ok else STRINGS[self.lang]["no_conn"])
        self.btn_prof_load.setStyleSheet("background-color: #81c995; color: #062e16; font-weight: 600;" if ok else "background-color: #f28b82; color: #3c0806; font-weight: 600;")
        self._log(STRINGS[self.lang]["log_pload"].format(name=name) if ok else STRINGS[self.lang]["log_err"], ok)
        QTimer.singleShot(1600, lambda: (self.btn_prof_load.setText(STRINGS[self.lang]["prof_load"]), self.btn_prof_load.setStyleSheet("")))

    def _on_delete_profile(self):
        name = self.cb_profiles.currentText()
        if not name:
            return
        if not self._ask(STRINGS[self.lang]["del_title"], STRINGS[self.lang]["del_q"].format(name=name)):
            return
        path = os.path.join(self._profiles_dir(), f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
        self._reload_profile_list()
        self._log(STRINGS[self.lang]["log_pdel"].format(name=name), True)
