import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('간단한 계산기')
        self.setGeometry(300, 300, 300, 200)

        layout = QVBoxLayout()
        self.result = QLineEdit()
        layout.addWidget(self.result)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        grid = QHBoxLayout()

        for button in buttons:
            btn = QPushButton(button)
            btn.clicked.connect(self.on_click)
            grid.addWidget(btn)
            if (buttons.index(button) + 1) % 4 == 0:
                layout.addLayout(grid)
                grid = QHBoxLayout()

        self.setLayout(layout)

    def on_click(self):
        button = self.sender().text()
        current = self.result.text()

        if button == '=':
            try:
                result = eval(current)
                self.result.setText(str(result))
            except:
                self.result.setText('오류')
        else:
            self.result.setText(current + button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec())