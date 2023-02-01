import sys

from lc_dielectrics import MainWindow
from qtpy.QtWidgets import QApplication


def main() -> None:
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
