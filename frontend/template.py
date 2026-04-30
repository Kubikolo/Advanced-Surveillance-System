import sys
import os
import json
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QGroupBox, QFormLayout, 
                               QListWidget, QMessageBox, QGraphicsView, 
                               QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
                               QGraphicsPixmapItem, QGraphicsPathItem, QCheckBox)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPointF
from PySide6.QtGui import QColor, QBrush, QPen, QMouseEvent, QPainter, QPixmap, QPainterPath

CELL_SIZE = 40
WONG_PALETTE = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#F0E442', '#56B4E9', '#E69F00']

class SimulationGraphicsView(QGraphicsView):
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
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)

    def zoom_in(self):
        self.scale(SimulationGraphicsView.scale_ratio, SimulationGraphicsView.scale_ratio)

    def zoom_out(self):
        self.scale(1 / SimulationGraphicsView.scale_ratio, 1 / SimulationGraphicsView.scale_ratio)

class SimulationWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.drone_artists = []
        self.frame = 0
        self.is_playing = True
        self.max_frames = 0
        
        self.load_data()
        self.init_ui()
        self.init_simulation()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

    def load_data(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_path, '..', 'shared', 'simulation_base.json')
        self.drone_img_path = os.path.join(base_path, 'drone.png')

        try:
            with open(json_path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"Could not find file: {json_path}")
            sys.exit(1)

        self.objects = self.data.get("objects", [])
        self.drones_data = self.data.get("drones", [])
        self.dimensions = self.data.get("dimensions", [10, 10])
        
        initial_steps_raw = self.data.get("initial_steps", [])
        loop_steps_raw = self.data.get("loop_steps", [])

        drone_count = len(self.drones_data) if self.drones_data else 1
        
        def normalize(data_list, count):
            if not data_list: return [[] for _ in range(count)]
            if not isinstance(data_list[0][0], (list, tuple)):
                res = [data_list]
                for _ in range(count - 1): res.append([])
                return res
            return data_list
            
        initial_paths = normalize(initial_steps_raw, drone_count)
        loop_paths = normalize(loop_steps_raw, drone_count)

        self.initial_paths = initial_paths
        self.loop_paths = loop_paths
        self.full_paths = []
        for i in range(drone_count):
            path = initial_paths[i] + loop_paths[i]
            self.full_paths.append(path)

    def init_ui(self):
        self.setWindowTitle('Advanced Surveillance Visualization')
        self.resize(1300, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        control_group = QGroupBox("Playback Controls")
        control_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        control_layout = QVBoxLayout()
        
        self.btn_play_pause = QPushButton("PAUSE")
        self.btn_play_pause.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_play_pause.clicked.connect(self.toggle_playback)
        
        self.lbl_frame = QLabel("Tick: 0")
        self.lbl_frame.setStyleSheet("color: #56B4E9; font-weight: bold; font-size: 14px;")
        
        control_layout.addWidget(self.btn_play_pause)
        control_layout.addWidget(self.lbl_frame)
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)

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
        
        self.view = SimulationGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid #444;")
        
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
        list_layout.addWidget(self.drone_list)
        
        self.list_group.setLayout(list_layout)
        right_layout.addWidget(self.list_group, 2)
        
        self.visibility_group = QGroupBox("Trail Visibility")
        self.visibility_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; padding-top: 15px; margin-top: 10px;}")
        self.vis_layout = QVBoxLayout()
        self.visibility_group.setLayout(self.vis_layout)
        right_layout.addWidget(self.visibility_group, 1)

        main_layout.addLayout(right_layout, 1)

    def init_simulation(self):
        width, height = self.dimensions[0], self.dimensions[1]

        grid_pen = QPen(QColor("#333333"))
        grid_brush = QBrush(QColor("#2b2b2b"))
        for row in range(height):
            for col in range(width):
                rect = QGraphicsRectItem(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                rect.setPen(grid_pen)
                rect.setBrush(grid_brush)
                self.scene.addItem(rect)

        obs_brush = QBrush(QColor("#E69F00"))
        obs_pen = QPen(QColor("#111111"))
        for obj in self.objects:
            for block in obj:
                rect = QGraphicsRectItem(block[0] * CELL_SIZE, block[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                rect.setBrush(obs_brush)
                rect.setPen(obs_pen)
                self.scene.addItem(rect)

        bound_pen = QPen(QColor("#FF3366"))
        bound_pen.setWidth(2)
        bound_pen.setStyle(Qt.PenStyle.DashLine)
        boundary = QGraphicsRectItem(0, 0, width * CELL_SIZE, height * CELL_SIZE)
        boundary.setPen(bound_pen)
        boundary.setZValue(5)
        self.scene.addItem(boundary)

        has_drone_img = os.path.exists(self.drone_img_path)
        raw_pixmap = QPixmap(self.drone_img_path) if has_drone_img else None

        margin = CELL_SIZE * 2
        self.scene.setSceneRect(-margin, -margin, width * CELL_SIZE + margin * 2, height * CELL_SIZE + margin * 2)

        for i, path in enumerate(self.full_paths):
            color_hex = WONG_PALETTE[i % len(WONG_PALETTE)]
            color = QColor(color_hex)
            
            drone_id = f"Drone {i+1}"
            self.drone_list.addItem(drone_id)

            chk = QCheckBox(f"Show {drone_id} Path")
            chk.setChecked(True)
            chk.setStyleSheet(f"color: {color_hex}; font-weight: bold;")
            chk.stateChanged.connect(lambda state, idx=i: self.toggle_trail(idx, state))
            self.vis_layout.addWidget(chk)

            trail_pen = QPen(color)
            trail_pen.setWidth(3)
            trail_path_item = QGraphicsPathItem()
            trail_path_item.setPen(trail_pen)
            trail_path_item.setZValue(8)
            self.scene.addItem(trail_path_item)

            d_config = self.drones_data[i] if i < len(self.drones_data) else {}
            radius = d_config.get("radius", 1)
            tickspeed = max(1, d_config.get("tickspeed", 1))

            vis_color = QColor(color)
            vis_color.setAlpha(40)
            vision_rect = QGraphicsRectItem(0, 0, radius * 2 * CELL_SIZE, radius * 2 * CELL_SIZE)
            vision_rect.setBrush(QBrush(vis_color))
            vision_rect.setPen(Qt.PenStyle.NoPen)
            vision_rect.setZValue(9)
            self.scene.addItem(vision_rect)

            if has_drone_img:
                scaled = raw_pixmap.scaled(CELL_SIZE, CELL_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                drone_item = QGraphicsPixmapItem(scaled)
                drone_item.setOffset(-scaled.width()/2, -scaled.height()/2)
            else:
                drone_item = QGraphicsEllipseItem(-CELL_SIZE/2, -CELL_SIZE/2, CELL_SIZE, CELL_SIZE)
                drone_item.setBrush(QBrush(color))
                drone_item.setPen(QPen(Qt.GlobalColor.white))
            
            drone_item.setZValue(10)
            self.scene.addItem(drone_item)

            self.drone_artists.append({
                'trail': trail_path_item,
                'vision': vision_rect,
                'drone': drone_item,
                'radius': radius,
                'initial': self.initial_paths[i],
                'loop': self.loop_paths[i],
                'tickspeed': tickspeed
            })

        QTimer.singleShot(100, lambda: self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))

    def toggle_playback(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play_pause.setText("PAUSE")
            self.btn_play_pause.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
            self.timer.start()
        else:
            self.btn_play_pause.setText("RESUME")
            self.btn_play_pause.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
            self.timer.stop()

    def toggle_trail(self, idx, state):
        is_checked = (state == 2)
        self.drone_artists[idx]['trail'].setVisible(is_checked)

    def update_frame(self):
        self.lbl_frame.setText(f"Tick: {self.frame:04d}")

        for art in self.drone_artists:
            eff_frame = self.frame // art['tickspeed']
            initial = art['initial']
            loop = art['loop']
            
            if not initial and not loop:
                continue
                
            if eff_frame < len(initial):
                pos = initial[eff_frame]
            elif loop:
                p_idx = (eff_frame - len(initial)) % len(loop)
                pos = loop[p_idx]
            else:
                pos = initial[-1]

            px = pos[0] * CELL_SIZE + CELL_SIZE / 2
            py = pos[1] * CELL_SIZE + CELL_SIZE / 2

            qpath = art['trail'].path()
            if qpath.elementCount() == 0:
                qpath.moveTo(px, py)
            else:
                qpath.lineTo(px, py)
            art['trail'].setPath(qpath)

            r_px = art['radius'] * CELL_SIZE
            art['vision'].setPos(px - r_px, py - r_px)
            art['drone'].setPos(px, py)

        self.frame += 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimulationWindow()
    window.show()
    sys.exit(app.exec())
