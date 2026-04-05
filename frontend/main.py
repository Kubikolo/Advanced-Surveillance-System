import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QGridLayout, QSpinBox, QLabel, QPushButton, QSizePolicy)
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import QSize

class GridButton(QPushButton):
    def __init__(self, area_icon, drone_icon):
        super().__init__()

        self.area_icon = area_icon
        self.drone_icon = drone_icon

        self.click_state = 0

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.clicked.connect(self.cycle_click)

    def cycle_click(self):
        self.click_state = (self.click_state + 1) % 3

        if self.click_state == 0:
            self.setIcon(QIcon())
        elif self.click_state == 1:
            self.setIcon(self.area_icon)
        elif self.click_state == 2:
            self.setIcon(self.drone_icon)

        self.setIconSize(QSize(40, 40))

class ConfigurationWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.x_size = 0
        self.y_size = 0
        
        self.area_icon = QIcon("assets/red.png")
        self.drone_icon = QIcon("assets/green.png")

        self.init_ui()

        self.update_grid()

    def init_ui(self):
        self.setWindowTitle('Configuration')
        self.resize(1200, 900)

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        left_layout.addWidget(QLabel("Enter x size"))
        self.input1 = QSpinBox()
        self.input1.setRange(0, 100) 
        self.input1.setValue(10)
        self.input1.valueChanged.connect(self.update_grid)
        left_layout.addWidget(self.input1)

        left_layout.addWidget(QLabel("Enter y size:"))
        self.input2 = QSpinBox()
        self.input2.setRange(0, 100)
        self.input2.setValue(10)
        self.input2.valueChanged.connect(self.update_grid)
        left_layout.addWidget(self.input2)

        left_layout.addStretch()

        main_layout.addLayout(left_layout, 1)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(2)
        
        main_layout.addWidget(self.grid_container, 4)


    def update_grid(self):
        self.x_size = self.input1.value()
        self.y_size = self.input2.value()

        self.clear_grid()

        for row in range(self.y_size):
            for col in range(self.x_size):
                cell = GridButton(self.area_icon, self.drone_icon)
                self.grid_layout.addWidget(cell, row, col)

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConfigurationWindow()
    window.show()
    sys.exit(app.exec())