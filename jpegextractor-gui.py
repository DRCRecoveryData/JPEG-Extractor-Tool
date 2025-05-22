import sys
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class JPEGRepairApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JPEG Extractor Tool")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        self.raw_label = QLabel("RAW Folder:")
        self.raw_path_edit = QLineEdit()
        self.raw_browse_button = QPushButton("Browse", self)
        self.raw_browse_button.setObjectName("browseButton")
        self.raw_browse_button.clicked.connect(self.browse_raw_folder)

        self.repaired_label = QLabel("Extracted Folder:")
        self.repaired_path_edit = QLineEdit()
        self.repaired_browse_button = QPushButton("Browse", self)
        self.repaired_browse_button.setObjectName("browseButton")
        self.repaired_browse_button.clicked.connect(self.browse_repaired_folder)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.extract_button = QPushButton("Extract", self)
        self.extract_button.setObjectName("blueButton")
        self.extract_button.clicked.connect(self.extract_jpeg_files)

        layout.addWidget(self.raw_label)
        layout.addWidget(self.raw_path_edit)
        layout.addWidget(self.raw_browse_button)
        layout.addWidget(self.repaired_label)
        layout.addWidget(self.repaired_path_edit)
        layout.addWidget(self.repaired_browse_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box)
        layout.addWidget(self.extract_button)

        self.setLayout(layout)

        self.setStyleSheet("""
        #browseButton, #blueButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 4px;
        }
        #browseButton:hover, #blueButton:hover {
            background-color: #2980b9;
        }
        """)

    def browse_raw_folder(self):
        raw_folder = QFileDialog.getExistingDirectory(self, "Select RAW Folder")
        if raw_folder:
            self.raw_path_edit.setText(raw_folder)

    def browse_repaired_folder(self):
        repaired_folder = QFileDialog.getExistingDirectory(self, "Select Extracted Folder")
        if repaired_folder:
            self.repaired_path_edit.setText(repaired_folder)

    def extract_jpeg_files(self):
        raw_folder_path = self.raw_path_edit.text()
        repaired_folder_path = self.repaired_path_edit.text()

        if not os.path.exists(raw_folder_path):
            self.show_message("Error", "RAW folder does not exist.")
            return

        if not os.path.exists(repaired_folder_path):
            os.makedirs(repaired_folder_path)

        self.worker = JPEGExtractionWorker(raw_folder_path, repaired_folder_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.update_log)
        self.worker.extraction_finished.connect(self.extraction_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_box.append(message)

    def extraction_finished(self, message):
        self.show_message("Extraction Complete", message)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)


class JPEGExtractionWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    extraction_finished = pyqtSignal(str)

    def __init__(self, raw_folder_path, repaired_folder_path):
        super().__init__()
        self.raw_folder_path = raw_folder_path
        self.repaired_folder_path = repaired_folder_path

    def run(self):
        files = [os.path.join(self.raw_folder_path, file) for file in os.listdir(self.raw_folder_path)
                 if file.lower().endswith((".arw", ".cr2", ".cr3", ".nef", ".jpg"))]

        total_files = len(files)
        if total_files == 0:
            self.extraction_finished.emit("No valid RAW files found.")
            return

        files_processed = 0

        for file in files:
            file_name = os.path.basename(file)
            self.log_updated.emit(f"Processing {file_name}...")
            extract_jpeg_from_raw(file, self.repaired_folder_path, self.log_updated.emit)
            self.log_updated.emit(f"{file_name} extraction attempt complete.")
            files_processed += 1
            progress = int((files_processed / total_files) * 100)
            self.progress_updated.emit(progress)

        self.extraction_finished.emit("JPEG extraction process completed.")


def extract_jpeg_from_raw(raw_file_path, repaired_folder, log_callback=None):
    try:
        with open(raw_file_path, 'rb') as raw_file:
            raw_data = raw_file.read()
    except Exception as e:
        msg = f"Failed to read file '{raw_file_path}': {e}"
        print(msg)
        if log_callback:
            log_callback(msg)
        return

    pattern_1 = re.compile(rb"\xFF\xD8\xFF[\xE0-\xEF].{2}Exif")  # Standard EXIF header
    pattern_2 = re.compile(rb"\xFF\xD8\xFF\xDB.{4,8}")  # General JPEG DQT marker

    start_positions = [m.start() for m in pattern_1.finditer(raw_data)]
    start_positions += [m.start() for m in pattern_2.finditer(raw_data)]
    start_positions.sort()

    if not start_positions:
        msg = f"No valid JPEG start markers found in '{raw_file_path}'."
        print(msg)
        if log_callback:
            log_callback(msg)
        return

    end_positions = []
    pos = raw_data.find(b'\xFF\xD9')
    while pos != -1:
        end_positions.append(pos + 2)  # Include \xFF\xD9
        pos = raw_data.find(b'\xFF\xD9', pos + 2)

    last_start, last_end = None, None
    for start_index in reversed(start_positions):
        end_index = next((end for end in reversed(end_positions) if end > start_index), None)
        if end_index:
            last_start = start_index
            last_end = end_index
            break

    if last_start is not None and last_end is not None:
        jpeg_data = raw_data[last_start:last_end]

        raw_file_name = os.path.splitext(os.path.basename(raw_file_path))[0]
        jpeg_file_path = os.path.join(repaired_folder, f"{raw_file_name}.JPG")

        try:
            with open(jpeg_file_path, 'wb') as jpeg_file:
                jpeg_file.write(jpeg_data)
            msg = f"Extracted JPEG saved to '{jpeg_file_path}'."
        except Exception as e:
            msg = f"Failed to save JPEG for '{raw_file_path}': {e}"
        print(msg)
        if log_callback:
            log_callback(msg)
    else:
        msg = f"Failed to extract valid JPEG from '{raw_file_path}'."
        print(msg)
        if log_callback:
            log_callback(msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JPEGRepairApp()
    window.show()
    sys.exit(app.exec())
