import sys
import traceback
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
    app.setStyle("Fusion")
    win = AjazzWindow()
    win.show()
    sys.exit(app.exec())
