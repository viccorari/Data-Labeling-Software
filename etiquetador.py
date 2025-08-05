import sys
import os
import csv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QInputDialog, QMessageBox,
    QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QComboBox,
    QFormLayout, QGroupBox
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QFont, QColor
from PySide6.QtCore import Qt, QRect, QPoint, QSize

# --- Diálogo para Gestionar Clases ---

class ManageLabelsDialog(QDialog):
    """Ventana para añadir, editar y eliminar las clases de objetos."""
    def __init__(self, labels, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Etiquetas")
        self.setMinimumSize(300, 400)

        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.original_labels = labels
        self.current_labels = list(self.original_labels.values())
        self.list_widget.addItems(self.current_labels)
        self.layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Añadir")
        self.edit_button = QPushButton("Editar")
        self.delete_button = QPushButton("Eliminar")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.button_box)

        self.add_button.clicked.connect(self.add_label)
        self.edit_button.clicked.connect(self.edit_label)
        self.delete_button.clicked.connect(self.delete_label)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Añadir Etiqueta", "Nombre de la nueva etiqueta:")
        if ok and text and text not in self.current_labels:
            self.current_labels.append(text)
            self.list_widget.addItem(text)

    def edit_label(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        old_text = selected_item.text()
        new_text, ok = QInputDialog.getText(self, "Editar Etiqueta", "Nuevo nombre:", text=old_text)
        if ok and new_text and new_text != old_text and new_text not in self.current_labels:
            index = self.current_labels.index(old_text)
            self.current_labels[index] = new_text
            selected_item.setText(new_text)

    def delete_label(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        reply = QMessageBox.question(self, "Eliminar Etiqueta", f"¿Estás seguro de que quieres eliminar '{selected_item.text()}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.current_labels.remove(selected_item.text())
            self.list_widget.takeItem(self.list_widget.row(selected_item))

    def get_updated_labels(self):
        return {i: name for i, name in enumerate(self.current_labels)}

# --- Diálogo para Seleccionar Etiqueta (Fallback) ---

class SelectAndConfirmDialog(QDialog):
    def __init__(self, class_map, yolo_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asignar Etiqueta")
        
        self.class_id = -1
        self.class_map = class_map
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.class_combo = QComboBox()
        self.class_combo.addItems(list(class_map.values()))
        
        form_layout.addRow("Etiqueta:", self.class_combo)
        
        _, x_center, y_center, width, height = yolo_data
        form_layout.addRow(QLabel("--- Datos YOLOv8 ---"))
        form_layout.addRow("x_center:", QLabel(f"{x_center:.6f}"))
        form_layout.addRow("y_center:", QLabel(f"{y_center:.6f}"))
        form_layout.addRow("width:", QLabel(f"{width:.6f}"))
        form_layout.addRow("height:", QLabel(f"{height:.6f}"))
        
        layout.addLayout(form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def accept(self):
        selected_text = self.class_combo.currentText()
        self.class_id = [k for k, v in self.class_map.items() if v == selected_text][0]
        super().accept()

# --- Widget de Imagen ---

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_pixmap = None
        self.scale_factor = 1.0
        self.pixmap_offset = QPoint(0, 0)
        self.scaled_pixmap_size = QSize()
        self.boxes = []
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selected_box_index = -1
        self.setMouseTracking(True)

    def setPixmap(self, pixmap):
        self.current_pixmap = pixmap
        self.update()

    def load_boxes(self, boxes):
        self.boxes = boxes
        self.set_selected_box(-1)
        self.update()

    def set_selected_box(self, index):
        self.selected_box_index = index
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_pixmap:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_pixmap:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            user_rect_on_widget = QRect(self.start_point, self.end_point).normalized()
            self.update()

            if not self.current_pixmap or self.current_pixmap.isNull(): return

            image_area_on_widget = QRect(self.pixmap_offset, self.scaled_pixmap_size)
            clipped_rect_on_widget = user_rect_on_widget.intersected(image_area_on_widget)

            if clipped_rect_on_widget.width() < 5 or clipped_rect_on_widget.height() < 5: return
            
            rect_on_image = QRect(clipped_rect_on_widget.topLeft() - self.pixmap_offset, clipped_rect_on_widget.size())

            if self.scale_factor > 0:
                original_rect = QRect(
                    int(rect_on_image.left() / self.scale_factor),
                    int(rect_on_image.top() / self.scale_factor),
                    int(rect_on_image.width() / self.scale_factor),
                    int(rect_on_image.height() / self.scale_factor)
                )
                self.process_new_box(original_rect)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.current_pixmap or self.current_pixmap.isNull(): return
        painter = QPainter(self)
        
        scaled_pixmap = self.current_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.scaled_pixmap_size = scaled_pixmap.size()
        self.scale_factor = scaled_pixmap.width() / self.current_pixmap.width() if self.current_pixmap.width() > 0 else 1
        self.pixmap_offset = QPoint((self.width() - self.scaled_pixmap_size.width()) // 2, (self.height() - self.scaled_pixmap_size.height()) // 2)
        
        painter.drawPixmap(self.pixmap_offset, scaled_pixmap)

        pen_saved = QPen(QColor(0, 255, 0), 2, Qt.PenStyle.SolidLine)
        pen_selected = QPen(QColor(255, 255, 0), 3, Qt.PenStyle.SolidLine)
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)

        for i, box_data in enumerate(self.boxes):
            rect_pixels, label = box_data['rect_pixels'], box_data['label']
            painter.setPen(pen_selected if i == self.selected_box_index else pen_saved)

            scaled_box = QRect(
                int(rect_pixels.left() * self.scale_factor), int(rect_pixels.top() * self.scale_factor),
                int(rect_pixels.width() * self.scale_factor), int(rect_pixels.height() * self.scale_factor)
            )
            scaled_box.translate(self.pixmap_offset)
            painter.drawRect(scaled_box)
            
            text_point = scaled_box.topLeft()
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(label)
            text_height = font_metrics.height()
            text_bg_rect = QRect(text_point.x(), text_point.y() - text_height, text_width + 4, text_height)
            
            bg_color = QColor(200, 200, 0, 180) if i == self.selected_box_index else QColor(0, 128, 0, 180)
            painter.fillRect(text_bg_rect, bg_color)
            painter.setPen(QColor(0,0,0) if i == self.selected_box_index else QColor(255,255,255))
            painter.drawText(text_point + QPoint(2, -3), label)

        if self.drawing:
            pen_drawing = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_drawing)
            painter.drawRect(QRect(self.start_point, self.end_point))

    def process_new_box(self, rect_pixels):
        class_map = self.main_window.class_map
        preselected_id = self.main_window.preselected_class_id

        img_w, img_h = self.current_pixmap.width(), self.current_pixmap.height()
        x_center = (rect_pixels.left() + rect_pixels.width() / 2) / img_w
        y_center = (rect_pixels.top() + rect_pixels.height() / 2) / img_h
        width = rect_pixels.width() / img_w
        height = rect_pixels.height() / img_h
        
        if preselected_id != -1:
            # Flujo rápido con preselección
            label = class_map[preselected_id]
            yolo_data = (preselected_id, x_center, y_center, width, height)
            self.main_window.add_new_box(rect_pixels, label, yolo_data)
        else:
            # Flujo normal con diálogo si no hay preselección
            if not class_map:
                QMessageBox.warning(self, "Sin Etiquetas", "Añada etiquetas usando 'Gestionar Etiquetas'.")
                return
            yolo_data_preview = (-1, x_center, y_center, width, height)
            dialog = SelectAndConfirmDialog(class_map, yolo_data_preview, self)
            if dialog.exec():
                class_id = dialog.class_id
                label = class_map[class_id]
                yolo_data = (class_id, x_center, y_center, width, height)
                self.main_window.add_new_box(rect_pixels, label, yolo_data)

# --- Ventana Principal ---

class LabelingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Herramienta de Etiquetado (Formato YOLOv8)")
        self.setGeometry(100, 100, 1200, 700)

        self.image_folder = ""
        self.labels_folder = "" # NUEVO: Carpeta para los archivos .txt
        self.image_files = []
        self.current_image_index = -1
        self.class_map = {}
        self.preselected_class_id = -1

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- Panel Izquierdo ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        top_bar_layout = QHBoxLayout()
        
        self.btn_select_folder = QPushButton("Seleccionar Carpeta")
        self.btn_manage_labels = QPushButton("Gestionar Etiquetas")
        self.btn_prev_image = QPushButton("<< Anterior")
        self.btn_next_image = QPushButton("Siguiente >>")
        
        top_bar_layout.addWidget(self.btn_select_folder)
        top_bar_layout.addWidget(self.btn_manage_labels)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.btn_prev_image)
        top_bar_layout.addWidget(self.btn_next_image)

        self.image_label = ImageLabel(self)
        self.status_label = QLabel("Selecciona una carpeta para comenzar.")
        
        left_layout.addLayout(top_bar_layout)
        left_layout.addWidget(self.image_label, 1)
        left_layout.addWidget(self.status_label)

        # --- Panel Derecho ---
        right_panel = QWidget()
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        
        # Grupo de Preselección
        preselect_group = QGroupBox("Seleccionar Etiqueta")
        preselect_layout = QVBoxLayout(preselect_group)
        self.class_selection_list = QListWidget()
        preselect_layout.addWidget(self.class_selection_list)
        
        # Grupo de Etiquetas en Imagen
        boxes_group = QGroupBox("Etiquetas en Imagen")
        boxes_layout = QVBoxLayout(boxes_group)
        self.boxes_list_widget = QListWidget()
        self.btn_delete_box = QPushButton("Eliminar Etiqueta Seleccionada")
        boxes_layout.addWidget(self.boxes_list_widget)
        boxes_layout.addWidget(self.btn_delete_box)

        right_layout.addWidget(preselect_group)
        right_layout.addWidget(boxes_group)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel)

        # --- Estilos ---
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2E2E2E; color: #F0F0F0; }
            QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 1ex; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QPushButton { background-color: #555; border: 1px solid #666; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #666; }
            QPushButton:pressed { background-color: #444; }
            QListWidget { border: 1px solid #555; background-color: #3C3C3C; }
            QListWidget::item:selected { background-color: #0078D7; color: white; }
            QLabel { color: #F0F0F0; }
        """)

        # --- Conexiones ---
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_manage_labels.clicked.connect(self.manage_labels)
        self.btn_prev_image.clicked.connect(self.prev_image)
        self.btn_next_image.clicked.connect(self.next_image)
        self.btn_delete_box.clicked.connect(self.delete_selected_box)
        self.boxes_list_widget.itemSelectionChanged.connect(self.highlight_selected_box)
        self.class_selection_list.itemSelectionChanged.connect(self.handle_class_preselection)

        self.update_button_states()

    def handle_class_preselection(self):
        selected_item = self.class_selection_list.currentItem()
        if selected_item:
            class_name = selected_item.text()
            self.preselected_class_id = [k for k, v in self.class_map.items() if v == class_name][0]
        else:
            self.preselected_class_id = -1
    
    def highlight_selected_box(self):
        self.image_label.set_selected_box(self.boxes_list_widget.currentRow())
        self.update_button_states()

    def update_button_states(self):
        has_images = bool(self.image_files)
        self.btn_prev_image.setEnabled(has_images and self.current_image_index > 0)
        self.btn_next_image.setEnabled(has_images and self.current_image_index < len(self.image_files) - 1)
        self.btn_manage_labels.setEnabled(bool(self.image_folder))
        self.btn_delete_box.setEnabled(self.boxes_list_widget.currentItem() is not None)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Imágenes")
        if folder:
            self.image_folder = folder
            # NUEVO: Definir y crear la carpeta de etiquetas
            self.labels_folder = os.path.join(self.image_folder, "Yolov8")
            os.makedirs(self.labels_folder, exist_ok=True)
            
            self.load_classes()
            self.load_image_list()
            if self.image_files:
                self.current_image_index = 0
                self.show_current_image()
            else:
                QMessageBox.warning(self, "Sin Imágenes", "La carpeta no contiene imágenes (.jpg, .png).")
                self.image_folder = ""
            self.update_button_states()

    def load_image_list(self):
        supported = ('.png', '.jpg', '.jpeg')
        self.image_files = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(supported)])
    
    def load_classes(self):
        path = os.path.join(self.image_folder, "classes.csv")
        if not os.path.exists(path):
            self.class_map = {0: "persona", 1: "pez"}
            self.save_classes()
        else:
            try:
                with open(path, mode='r', newline='', encoding='utf-8') as f:
                    self.class_map = {int(r[0]): r[1] for r in csv.reader(f)}
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer 'classes.csv': {e}")
                self.class_map = {}
        self.populate_class_selection_list()

    def populate_class_selection_list(self):
        self.class_selection_list.clear()
        self.class_selection_list.addItems(list(self.class_map.values()))

    def save_classes(self):
        path = os.path.join(self.image_folder, "classes.csv")
        try:
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for class_id, name in self.class_map.items():
                    writer.writerow([class_id, name])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar 'classes.csv': {e}")

    def manage_labels(self):
        dialog = ManageLabelsDialog(self.class_map, self)
        if dialog.exec():
            self.class_map = dialog.get_updated_labels()
            self.save_classes()
            self.populate_class_selection_list()

    def show_current_image(self):
        if 0 <= self.current_image_index < len(self.image_files):
            image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap)
            self.status_label.setText(f"Imagen {self.current_image_index + 1}/{len(self.image_files)}: {self.image_files[self.current_image_index]}")
            self.load_boxes_for_current_image()
        self.update_button_states()

    def next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.show_current_image()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            
    def add_new_box(self, rect_pixels, label, yolo_data):
        yolo_line = f"{yolo_data[0]} {yolo_data[1]:.6f} {yolo_data[2]:.6f} {yolo_data[3]:.6f} {yolo_data[4]:.6f}"
        self.append_to_yolo_txt(yolo_line)
        self.load_boxes_for_current_image()
        
    def append_to_yolo_txt(self, yolo_line):
        filename_base = os.path.splitext(self.image_files[self.current_image_index])[0]
        # MODIFICADO: Usa la carpeta de etiquetas
        txt_path = os.path.join(self.labels_folder, filename_base + ".txt")
        try:
            with open(txt_path, mode='a', encoding='utf-8') as f:
                f.write(yolo_line + "\n")
        except IOError as e:
            QMessageBox.critical(self, "Error de Escritura", f"No se pudo guardar en .txt:\n{e}")
            
    def load_boxes_for_current_image(self):
        boxes = []
        self.boxes_list_widget.clear()
        filename_base = os.path.splitext(self.image_files[self.current_image_index])[0]
        # MODIFICADO: Usa la carpeta de etiquetas
        txt_path = os.path.join(self.labels_folder, filename_base + ".txt")
        
        if os.path.exists(txt_path):
            try:
                img_w, img_h = self.image_label.current_pixmap.width(), self.image_label.current_pixmap.height()
                with open(txt_path, 'r') as f:
                    for line in f:
                        if not line.strip(): continue
                        parts = line.strip().split()
                        class_id, x_c, y_c, w, h = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                        
                        rect = QRect(int((x_c - w/2) * img_w), int((y_c - h/2) * img_h), int(w * img_w), int(h * img_h))
                        label = self.class_map.get(class_id, f"ID:{class_id}?")
                        
                        box_data = {'rect_pixels': rect, 'label': label, 'yolo_line': line.strip()}
                        boxes.append(box_data)

                        item = QListWidgetItem(f"ID: {class_id} - {label}")
                        item.setData(Qt.ItemDataRole.UserRole, line.strip())
                        self.boxes_list_widget.addItem(item)
            except Exception as e:
                print(f"Error leyendo el archivo .txt: {e}")

        self.image_label.load_boxes(boxes)
        self.update_button_states()

    def delete_selected_box(self):
        selected_item = self.boxes_list_widget.currentItem()
        if not selected_item: return

        line_to_delete = selected_item.data(Qt.ItemDataRole.UserRole)
        filename_base = os.path.splitext(self.image_files[self.current_image_index])[0]
        # MODIFICADO: Usa la carpeta de etiquetas
        txt_path = os.path.join(self.labels_folder, filename_base + ".txt")

        try:
            with open(txt_path, 'r') as f: lines = f.readlines()
            with open(txt_path, 'w') as f:
                for line in lines:
                    if line.strip() != line_to_delete: f.write(line)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo modificar el archivo .txt: {e}")
            return
        
        self.load_boxes_for_current_image()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LabelingApp()
    window.show()
    sys.exit(app.exec())
