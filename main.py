import sys
import traceback
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from ajazz_app.gui import AjazzWindow

def handle_exception(exc_type, exc_value, exc_tb):
    err_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("\n=== CRASH LOG ===\n", err_text)
    with open("crash.log", "w", encoding="utf-8") as f:
        f.write(err_text)
    QMessageBox.critical(None, "Ошибка приложения", err_text)

sys.excepthook = handle_exception

if __name__ == "__main__":
    app = QApplication(sys.argv)
    _bd = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for _p in (os.path.join(_bd, "assets", "icon.ico"), os.path.join(_bd, "icon.ico"), os.path.join(_bd, "assets", "icon.png"), os.path.join(_bd, "icon.png")):
        if os.path.exists(_p):
            app.setWindowIcon(QIcon(_p))
            break
    app.setStyle("Fusion")
    win = AjazzWindow()
    win.show()
    sys.exit(app.exec())
