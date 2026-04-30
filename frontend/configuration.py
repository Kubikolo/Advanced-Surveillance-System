import sys
import os
import json
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSpinBox, QLabel, QPushButton, QGroupBox, QFormLayout, 
                               QRadioButton, QButtonGroup, QMessageBox, QGraphicsView, 
                               QGraphicsScene, QGraphicsRectItem, 
                               QGraphicsPixmapItem, QListWidget, QFileDialog)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QMouseEvent, QPainter, QPixmap

CELL_SIZE = 40

class GridItem(QGraphicsRectItem):
    def __init__(self, row, col,  drone_pixmap = None, field_pixmap = None):
        super().__init__(0, 0, CELL_SIZE, CELL_SIZE)
        self.row = row
        self.col = col
        self.setPos(col * CELL_SIZE, row * CELL_SIZE)

        self.dron_pixmap = drone_pixmap
        self.field_pixmap = field_pixmap

        self.cell_type = "empty"

        self.pixmap = QGraphicsPixmapItem(self)

        self.update_appearance()

    def update_appearance(self):
        pen = QPen(QColor("#333333"))
        self.setPen(pen)

        self.pixmap.setPixmap(QPixmap())

        if self.cell_type == "empty":
            self.setBrush(QBrush(QColor("#2b2b2b")))
            
        elif self.cell_type == "field":
            self.setBrush(QBrush(QColor("#4a90e2")))
            
            if hasattr(self, 'field_pixmap') and self.field_pixmap and not self.field_pixmap.isNull():
                self.pixmap.setPixmap(self.field_pixmap)
                
                rect = self.pixmap.boundingRect()
                self.pixmap.setPos((CELL_SIZE - rect.width()) / 2, (CELL_SIZE - rect.height()) / 2)
            
        elif self.cell_type == "drone":
            self.setBrush(QBrush(QColor("#50e3c2")))
            
            if hasattr(self, 'drone_pixmap') and self.drone_pixmap and not self.drone_pixmap.isNull():
                self.pixmap.setPixmap(self.drone_pixmap)
                
                rect = self.pixmap.boundingRect()
                self.pixmap.setPos((CELL_SIZE - rect.width()) / 2, (CELL_SIZE - rect.height()) / 2)


class InteractiveGraphicsView(QGraphicsView):
    cell_clicked = Signal(int, int)
    cell_dragged = Signal(int, int)
    scale_ratio = 1.2

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            fake_event = QMouseEvent(event.type(), event.position(), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, event.modifiers())
            super().mousePressEvent(fake_event)
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())

            if isinstance(item, QGraphicsPixmapItem):
                item = item.parentItem()
            if isinstance(item, GridItem):
                self.cell_clicked.emit(item.row, item.col)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragMode() != QGraphicsView.DragMode.ScrollHandDrag:
            item = self.itemAt(event.position().toPoint())
            
            if isinstance(item, QGraphicsPixmapItem):
                item = item.parentItem()
            if isinstance(item, GridItem):
                self.cell_dragged.emit(item.row, item.col)
                
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        super().mouseReleaseEvent(event)

    def zoom_in(self):
        self.scale(InteractiveGraphicsView.scale_ratio, InteractiveGraphicsView.scale_ratio)

    def zoom_out(self):
        self.scale(1 / InteractiveGraphicsView.scale_ratio, 1 / InteractiveGraphicsView.scale_ratio)


class ConfigurationWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.x_size = 20
        self.y_size = 20
        
        self.drones = {}
        self.radius_overlays = {}
        self.active_drone_pos = None
        
        self.drone_counter = 1
        self.last_dragged_cell = None

        self.drone_pixmap = self.loadImageOrDefault("assets/drone.png")
        self.field_pixmap = self.loadImageOrDefault("assets/field.png")

        self.init_ui()
        self.update_grid()

    def init_ui(self):
        self.setWindowTitle('Drone Simulation Configurator v7')
        self.resize(1300, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        size_group = QGroupBox("Grid Dimensions")
        size_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        size_layout = QFormLayout()
        
        self.spin_x = QSpinBox()
        self.spin_x.setRange(5, 100)
        self.spin_x.setValue(self.x_size)
        self.spin_x.setStyleSheet("background-color: #333; padding: 5px;")
        
        self.spin_y = QSpinBox()
        self.spin_y.setRange(5, 100)
        self.spin_y.setValue(self.y_size)
        self.spin_y.setStyleSheet("background-color: #333; padding: 5px;")
        
        btn_update = QPushButton("Generate Grid")
        btn_update.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        btn_update.clicked.connect(self.update_grid)

        size_layout.addRow("Width (X):", self.spin_x)
        size_layout.addRow("Height (Y):", self.spin_y)
        size_layout.addRow(btn_update)
        size_group.setLayout(size_layout)
        left_layout.addWidget(size_group)

        tool_group = QGroupBox("Tools")
        tool_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        tool_layout = QVBoxLayout()
        
        self.tool_group = QButtonGroup(self)
        tools = [
            ("Add Field", "field"),
            ("Remove", "empty")
        ]
        
        self.radio_buttons = {}
        for idx, (text, mode) in enumerate(tools):
            radio = QRadioButton(text)
            if mode == "field":
                radio.setChecked(True)
            self.tool_group.addButton(radio, idx)
            self.radio_buttons[idx] = mode
            tool_layout.addWidget(radio)
            
        tool_group.setLayout(tool_layout)
        left_layout.addWidget(tool_group)
        
        btn_export = QPushButton("Export to JSON")
        btn_export.setStyleSheet("background-color: #007ACC; color: white; padding: 10px; font-weight: bold; margin-top: 20px;")
        btn_export.clicked.connect(self.export_to_json)
        left_layout.addWidget(btn_export)

        left_layout.addStretch()
        main_layout.addLayout(left_layout, 1)

        center_layout = QVBoxLayout()
        
        zoom_layout = QHBoxLayout()
        lbl_zoom = QLabel("Use Ctrl+Scroll or MMB-Drag to pan")
        lbl_zoom.setStyleSheet("color: #888;")
        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_out = QPushButton("Zoom -")
        btn_zoom_in.setStyleSheet("background-color: #444; padding: 5px;")
        btn_zoom_out.setStyleSheet("background-color: #444; padding: 5px;")
        zoom_layout.addWidget(lbl_zoom)
        zoom_layout.addStretch()
        zoom_layout.addWidget(btn_zoom_out)
        zoom_layout.addWidget(btn_zoom_in)
        
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor("#121212"))
        
        self.view = InteractiveGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid #444;")
        self.view.cell_clicked.connect(self.on_cell_clicked)
        self.view.cell_dragged.connect(self.on_cell_dragged) 
        
        btn_zoom_in.clicked.connect(self.view.zoom_in)
        btn_zoom_out.clicked.connect(self.view.zoom_out)

        center_layout.addLayout(zoom_layout)
        center_layout.addWidget(self.view)
        
        main_layout.addLayout(center_layout, 5)

        right_layout = QVBoxLayout()
        
        self.list_group = QGroupBox("Active Drones")
        self.list_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        list_layout = QVBoxLayout()
        
        self.drone_list = QListWidget()
        self.drone_list.setStyleSheet("background-color: #333; padding: 5px;")
        self.drone_list.currentItemChanged.connect(self.on_drone_selected)
        list_layout.addWidget(self.drone_list)
        
        list_btn_layout = QHBoxLayout()
        btn_add_drone_list = QPushButton("Add Drone")
        btn_add_drone_list.setStyleSheet("background-color: #444; padding: 5px;")
        btn_add_drone_list.clicked.connect(self.add_drone_from_list)
        
        btn_remove_drone_list = QPushButton("Remove drone")
        btn_remove_drone_list.setStyleSheet("background-color: #444; padding: 5px;")
        btn_remove_drone_list.clicked.connect(self.remove_drone_from_list)
        
        list_btn_layout.addWidget(btn_add_drone_list)
        list_btn_layout.addWidget(btn_remove_drone_list)
        list_layout.addLayout(list_btn_layout)
        
        self.list_group.setLayout(list_layout)
        
        self.prop_group = QGroupBox("Drone Properties")
        self.prop_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        prop_layout = QFormLayout()
        
        self.lbl_pos = QLabel("Select a drone from the list.")
        self.lbl_pos.setStyleSheet("color: #aaa; font-style: italic; margin-bottom: 5px;")
        
        self.spin_pos_x = QSpinBox()
        self.spin_pos_x.setEnabled(False)
        self.spin_pos_x.setStyleSheet("background-color: #333; padding: 5px;")
        self.spin_pos_x.valueChanged.connect(self.move_drone)

        self.spin_pos_y = QSpinBox()
        self.spin_pos_y.setEnabled(False)
        self.spin_pos_y.setStyleSheet("background-color: #333; padding: 5px;")
        self.spin_pos_y.valueChanged.connect(self.move_drone)

        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(1, 100)
        self.spin_speed.setEnabled(False)
        self.spin_speed.setStyleSheet("background-color: #333; padding: 5px;")
        self.spin_speed.valueChanged.connect(self.save_drone_params)
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 50)
        self.spin_radius.setEnabled(False)
        self.spin_radius.setStyleSheet("background-color: #333; padding: 5px;")
        self.spin_radius.valueChanged.connect(self.save_drone_params)
        
        prop_layout.addRow(self.lbl_pos)
        prop_layout.addRow("Pos X (Col):", self.spin_pos_x)
        prop_layout.addRow("Pos Y (Row):", self.spin_pos_y)
        prop_layout.addRow("Speed (m/s):", self.spin_speed)
        prop_layout.addRow("Radius (m):", self.spin_radius)
        self.prop_group.setLayout(prop_layout)
        
        right_layout.addWidget(self.list_group, 2)
        right_layout.addWidget(self.prop_group, 1)
        
        main_layout.addLayout(right_layout, 1)

    def loadImageOrDefault(self, image_path):
        pixmap = None
        if os.path.exists(image_path):
            raw_pixmap = QPixmap(image_path)
            pixmap = raw_pixmap.scaled(CELL_SIZE - 8, CELL_SIZE - 8, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            pixmap = QPixmap()
        return pixmap

    def update_grid(self):
        self.x_size = self.spin_x.value()
        self.y_size = self.spin_y.value()
        
        self.spin_pos_x.setRange(0, self.x_size - 1)
        self.spin_pos_y.setRange(0, self.y_size - 1)

        self.scene.clear()
        self.drones.clear()
        self.radius_overlays.clear()
        self.drone_list.clear()
        self.drone_counter = 1
        self.disable_properties()

        self.grid_items = {}
        for row in range(self.y_size):
            for col in range(self.x_size):
                cell = GridItem(row, col, self.drone_pixmap, self.field_pixmap)
                self.scene.addItem(cell)
                self.grid_items[(row, col)] = cell

    def on_cell_clicked(self, row, col):
        self.last_dragged_cell = (row, col)
        self.apply_tool(row, col)

    def on_cell_dragged(self, row, col):
        if self.last_dragged_cell == (row, col):
            return
        self.last_dragged_cell = (row, col)
        self.apply_tool(row, col)

    def apply_tool(self, row, col, override_mode=None):
        if override_mode:
            mode = override_mode
        else:
            tool_id = self.tool_group.checkedId()
            mode = self.radio_buttons[tool_id]
        
        cell = self.grid_items.get((row, col))
        if not cell: return

        if cell.cell_type == "drone" and mode != "drone":
            drone_data = self.drones.pop((row, col), None)
            
            if drone_data:
                items = self.drone_list.findItems(drone_data['id'], Qt.MatchFlag.MatchExactly)
                if items:
                    self.drone_list.takeItem(self.drone_list.row(items[0]))
            
            if self.active_drone_pos == (row, col):
                self.disable_properties()
                
            if (row, col) in self.radius_overlays:
                self.scene.removeItem(self.radius_overlays[(row, col)])
                del self.radius_overlays[(row, col)]

        if cell.cell_type == "drone" and mode == "drone":
            return

        cell.cell_type = mode
        cell.update_appearance()

        if mode == "drone":
            drone_id = f"Drone {self.drone_counter}"
            self.drone_counter += 1
            
            self.drones[(row, col)] = {'speed': 10, 'radius': 3, 'id': drone_id}
            self.drone_list.addItem(drone_id)
            self.create_radius_overlay(row, col)
            
            items = self.drone_list.findItems(drone_id, Qt.MatchFlag.MatchExactly)
            if items:
                self.drone_list.setCurrentItem(items[0])

    def add_drone_from_list(self):
        for row in range(self.y_size):
            for col in range(self.x_size):
                cell = self.grid_items.get((row, col))
                if cell and cell.cell_type == "empty":
                    self.apply_tool(row, col, override_mode="drone")
                    return
        QMessageBox.warning(self, "Grid Full", "There is no empty space to place a new drone.")

    def remove_drone_from_list(self):
        current = self.drone_list.currentItem()
        if not current:
            return
            
        selected_id = current.text()
        
        for (row, col), data in list(self.drones.items()):
            if data['id'] == selected_id:
                self.apply_tool(row, col, override_mode="empty")
                break

    def on_drone_selected(self, current, previous):
        if not current:
            self.disable_properties()
            return
            
        selected_id = current.text()
        
        for (row, col), data in self.drones.items():
            if data['id'] == selected_id:
                self.load_drone_params(row, col)
                return

    def create_radius_overlay(self, row, col):
        brush = QBrush(QColor(255, 80, 80, 127))
        pen = QPen(QColor(255, 50, 50, 200))
        pen.setWidth(2)
        
        overlay = QGraphicsRectItem()
        overlay.setBrush(brush)
        overlay.setPen(pen)
        
        overlay.setAcceptedMouseButtons(Qt.MouseButton.NoButton) 
        overlay.setZValue(1) 
        
        self.scene.addItem(overlay)
        self.radius_overlays[(row, col)] = overlay
        self.update_radius_overlay(row, col)

    def update_radius_overlay(self, row, col):
        if (row, col) not in self.radius_overlays: return
        
        radius = self.drones[(row, col)]['radius']
        overlay = self.radius_overlays[(row, col)]
        
        center_x = (col * CELL_SIZE) + (CELL_SIZE / 2)
        center_y = (row * CELL_SIZE) + (CELL_SIZE / 2)
        r_px = radius * CELL_SIZE
        
        overlay.setRect(QRectF(center_x - r_px, center_y - r_px, r_px * 2, r_px * 2))
    
    def load_drone_params(self, row, col):
        self.active_drone_pos = (row, col)
        data = self.drones.get((row, col), {'speed': 10, 'radius': 3})
        
        self.lbl_pos.setText(f"Editing: {data['id']}")
        self.lbl_pos.setStyleSheet("color: #50e3c2; font-weight: bold; margin-bottom: 5px;")
        
        self.spin_pos_x.blockSignals(True)
        self.spin_pos_y.blockSignals(True)
        self.spin_speed.blockSignals(True)
        self.spin_radius.blockSignals(True)
        
        self.spin_pos_x.setValue(col)
        self.spin_pos_y.setValue(row)
        self.spin_speed.setValue(data['speed'])
        self.spin_radius.setValue(data['radius'])
        
        self.spin_pos_x.blockSignals(False)
        self.spin_pos_y.blockSignals(False)
        self.spin_speed.blockSignals(False)
        self.spin_radius.blockSignals(False)
        
        self.spin_pos_x.setEnabled(True)
        self.spin_pos_y.setEnabled(True)
        self.spin_speed.setEnabled(True)
        self.spin_radius.setEnabled(True)

    def move_drone(self):
        if not self.active_drone_pos:
            return
            
        old_row, old_col = self.active_drone_pos
        new_row = self.spin_pos_y.value()
        new_col = self.spin_pos_x.value()
        
        if (old_row, old_col) == (new_row, new_col):
            return
            
        target_cell = self.grid_items.get((new_row, new_col))
        
        if target_cell and target_cell.cell_type == "drone":
            self.spin_pos_y.blockSignals(True)
            self.spin_pos_x.blockSignals(True)
            self.spin_pos_y.setValue(old_row)
            self.spin_pos_x.setValue(old_col)
            self.spin_pos_y.blockSignals(False)
            self.spin_pos_x.blockSignals(False)
            QMessageBox.warning(self, "Invalid Move", "A drone is already located at this position.")
            return

        drone_data = self.drones.pop((old_row, old_col))
        
        old_cell = self.grid_items.get((old_row, old_col))
        if old_cell:
            old_cell.cell_type = "empty"
            old_cell.update_appearance()
            
        if target_cell:
            target_cell.cell_type = "drone"
            target_cell.update_appearance()
            
        self.active_drone_pos = (new_row, new_col)
        self.drones[(new_row, new_col)] = drone_data
        
        overlay = self.radius_overlays.pop((old_row, old_col))
        self.radius_overlays[(new_row, new_col)] = overlay
        self.update_radius_overlay(new_row, new_col)

    def save_drone_params(self):
        if self.active_drone_pos in self.drones:
            self.drones[self.active_drone_pos]['speed'] = self.spin_speed.value()
            self.drones[self.active_drone_pos]['radius'] = self.spin_radius.value()
            self.update_radius_overlay(*self.active_drone_pos)

    def disable_properties(self):
        self.active_drone_pos = None
        self.lbl_pos.setText("Select a drone from the list.")
        self.lbl_pos.setStyleSheet("color: #aaa; font-style: italic; margin-bottom: 5px;")
        
        self.spin_pos_x.setEnabled(False)
        self.spin_pos_y.setEnabled(False)
        self.spin_speed.setEnabled(False)
        self.spin_radius.setEnabled(False)
        
        self.spin_pos_x.setValue(0)
        self.spin_pos_y.setValue(0)
        self.spin_speed.setValue(0)
        self.spin_radius.setValue(0)

    def export_to_json(self):
        drones_output = []
        for (row, col), data in self.drones.items():
            drones_output.append({
                "starting_position": [col, row],
                "radius": data['radius'],
                "tickspeed": data['speed']
            })

        unvisited_fields = set()
        for (row, col), cell in self.grid_items.items():
            if cell.cell_type == "field":
                unvisited_fields.add((row, col))
                
        objects_output = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while unvisited_fields:
            start_node = unvisited_fields.pop()
            current_component = [[start_node[1], start_node[0]]]
            queue = [start_node]
            
            while queue:
                row, col = queue.pop(0)
                for dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    if (new_row, new_col) in unvisited_fields:
                        unvisited_fields.remove((new_row, new_col))
                        queue.append((new_row, new_col))
                        current_component.append([new_col, new_row])
                        
            objects_output.append(current_component)

        export_data = {
            "objects": objects_output,
            "drones": drones_output,
            "dimensions": [self.x_size, self.y_size]
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Configuration", 
            "drone_config.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as json_file:
                    json.dump(export_data, json_file, indent=2)
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = ConfigurationWindow()
    window.show()
    sys.exit(app.exec())