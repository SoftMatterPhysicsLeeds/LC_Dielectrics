import sys

from qtpy.QtWidgets import QApplication

from lcdielectrics.lc_dielectrics import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    main()
