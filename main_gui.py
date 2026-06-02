import sys
import copy
import math
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QWidget, QGridLayout, QGroupBox, QTextEdit,
    QProgressBar, QStatusBar
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from lzw_utils import (
    header_to_binary_string, binary_string_to_header,
    encode_progressive, decode_progressive,
    pad_encoded_text, get_byte_array, remove_padding
)
from level1_text import TextLZW
from level2_grayscale import GrayscaleImageLZW
from level3_compression import Level3GrayDiffLZW
from level4_color_compression import ColorImageLZW
from level5_color_diff_compression import ColorDiffLZW

class CompressionWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, task_fn, *args, **kwargs):
        super().__init__()
        self._task_fn = task_fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._task_fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))

def compute_psnr_mse(original: np.ndarray, restored: np.ndarray) -> tuple[float, float]:
    orig = original.astype(np.float64)
    rest = restored.astype(np.float64)
    if orig.shape != rest.shape:
        return float("nan"), float("nan")
    mse = float(np.mean((orig - rest) ** 2))
    if mse == 0:
        return 0.0, float("inf")
    psnr = 10 * math.log10((255.0 ** 2) / mse)
    return mse, psnr

class LZWImageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LZW Image and Text Compression")
        self.setGeometry(100, 100, 1200, 800)

        self.lzw_l1 = TextLZW(codelength=16)
        self.lzw_l2 = GrayscaleImageLZW(codelength=16)
        self.lzw_l3 = Level3GrayDiffLZW(codelength=16)
        self.lzw_l4 = ColorImageLZW(codelength=16)
        self.lzw_l5 = ColorDiffLZW(codelength=16)

        self.loaded_file_path: str | None = None
        self.loaded_text: str | None = None
        self.original_img: np.ndarray | None = None
        self.compressed_data = None
        self.compressed_bytes: bytearray | None = None
        self.current_level: int | None = None
        self.decompressed_img: np.ndarray | None = None
        self.decompressed_text: str | None = None
        self._worker: QThread | None = None

        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        display_layout = QVBoxLayout()

        self.txt_original = QTextEdit()
        self.txt_original.setReadOnly(True)
        self.txt_original.hide()

        self.lbl_original = QLabel("Original Image / Text")
        self.lbl_original.setAlignment(Qt.AlignCenter)
        self.lbl_original.setStyleSheet("border: 1px solid #999; background: #f5f5f5;")
        self.lbl_original.setMinimumSize(480, 300)

        self.txt_decompressed = QTextEdit()
        self.txt_decompressed.setReadOnly(True)
        self.txt_decompressed.hide()

        self.lbl_decompressed = QLabel("Decompressed Image / Text")
        self.lbl_decompressed.setAlignment(Qt.AlignCenter)
        self.lbl_decompressed.setStyleSheet("border: 1px solid #999; background: #f5f5f5;")
        self.lbl_decompressed.setMinimumSize(480, 300)

        display_layout.addWidget(QLabel("<b>Original Data:</b>"))
        display_layout.addWidget(self.lbl_original)
        display_layout.addWidget(self.txt_original)
        display_layout.addWidget(QLabel("<b>Decompressed Data:</b>"))
        display_layout.addWidget(self.lbl_decompressed)
        display_layout.addWidget(self.txt_decompressed)

        control_layout = QVBoxLayout()
        control_layout.setSpacing(8)

        file_group = QGroupBox("1. File Operations")
        file_vbox = QVBoxLayout()
        btn_load_file = QPushButton("Load Data (.png, .bmp, .txt)")
        btn_load_file.clicked.connect(self.load_file)
        btn_load_comp = QPushButton("Load Compressed File (.lzw)")
        btn_load_comp.clicked.connect(self.load_compressed_file)
        file_vbox.addWidget(btn_load_file)
        file_vbox.addWidget(btn_load_comp)
        file_group.setLayout(file_vbox)

        comp_group = QGroupBox("2. Compression Method")
        comp_grid = QGridLayout()
        btn_l1 = QPushButton("Level 1 - Text")
        btn_l2 = QPushButton("Level 2 - Grayscale")
        btn_l3 = QPushButton("Level 3 - Gray + Diff")
        btn_l4 = QPushButton("Level 4 - Color")
        btn_l5 = QPushButton("Level 5 - Color + Diff")

        for level, btn in enumerate([btn_l1, btn_l2, btn_l3, btn_l4, btn_l5], start=1):
            btn.clicked.connect(lambda checked, lv=level: self.run_compression(lv))

        comp_grid.addWidget(btn_l1, 0, 0, 1, 2)
        comp_grid.addWidget(btn_l2, 1, 0)
        comp_grid.addWidget(btn_l3, 1, 1)
        comp_grid.addWidget(btn_l4, 2, 0)
        comp_grid.addWidget(btn_l5, 2, 1)
        comp_group.setLayout(comp_grid)

        action_group = QGroupBox("3. Actions")
        action_vbox = QVBoxLayout()
        btn_save_comp = QPushButton("Save Compressed Data")
        btn_decompress = QPushButton("Decompress")
        btn_save_restored = QPushButton("Save Decompressed File")
        btn_save_comp.clicked.connect(self.save_compressed_file)
        btn_decompress.clicked.connect(self.run_decompression)
        btn_save_restored.clicked.connect(self.save_restored_file)
        action_vbox.addWidget(btn_save_comp)
        action_vbox.addWidget(btn_decompress)
        action_vbox.addWidget(btn_save_restored)
        action_group.setLayout(action_vbox)

        metrics_group = QGroupBox("Metrics")
        metrics_vbox = QVBoxLayout()
        self.lbl_size_orig = QLabel("Original Size: -")
        self.lbl_size_comp = QLabel("Compressed Size: -")
        self.lbl_entropy = QLabel("Entropy: -")
        self.lbl_cr = QLabel("CR: - | CF: - | SS: -")
        self.lbl_psnr = QLabel("PSNR: - | MSE: -")

        for lbl in [self.lbl_size_orig, self.lbl_size_comp,
                    self.lbl_entropy, self.lbl_cr, self.lbl_psnr]:
            lbl.setStyleSheet("font-family: monospace;")
            metrics_vbox.addWidget(lbl)
        metrics_group.setLayout(metrics_vbox)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()

        control_layout.addWidget(file_group)
        control_layout.addWidget(comp_group)
        control_layout.addWidget(action_group)
        control_layout.addWidget(metrics_group)
        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()

        main_layout.addLayout(display_layout, 3)
        main_layout.addLayout(control_layout, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Please load a file.")

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Data", "",
            "Supported Files (*.png *.bmp *.txt);;Image (*.png *.bmp);;Text (*.txt)"
        )
        if not file_name:
            return
        self.loaded_file_path = file_name
        self._reset_output_state()

        try:
            if file_name.lower().endswith('.txt'):
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.loaded_text = f.read()
                self.original_img = None
                self._show_text_mode()
                self.txt_original.setText(self.loaded_text)
            else:
                img = cv2.imread(file_name)
                if img is None:
                    raise ValueError("Failed to read image. Check file format.")
                self.original_img = img
                self.loaded_text = None
                self._show_image_mode()
                self._display_image(img, self.lbl_original)

            self.status_bar.showMessage(f"Loaded: {file_name}")
            QMessageBox.information(self, "Success", "File loaded! Please select a compression method.")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not load file:\n{exc}")

    def run_compression(self, level: int):
        if not self.loaded_file_path:
            QMessageBox.warning(self, "Warning", "Please load a file first!")
            return
        if level == 1 and self.loaded_text is None:
            QMessageBox.warning(self, "Warning", "Level 1 requires a .txt file.")
            return
        if level in (2, 3, 4, 5) and self.original_img is None:
            QMessageBox.warning(self, "Warning", f"Level {level} requires a .png or .bmp image.")
            return

        self.current_level = level
        self._set_busy(True)

        self._worker = CompressionWorker(self._compress_task, level)
        self._worker.finished.connect(self._on_compression_done)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _compress_task(self, level: int) -> dict:
        h = w = l1 = l2 = l3 = 0
        orig_size = entropy = 0
        bit_data = ""

        if level == 1:
            codes, _ = self.lzw_l1.compress(self.loaded_text)
            orig_size = len(self.loaded_text)
            entropy = self.lzw_l1.calculate_entropy(self.loaded_text)
            l1 = len(codes)
            bit_data = encode_progressive(codes, 256, 16)
            compressed_data = codes
        elif level == 2:
            comp_data, img = self.lzw_l2.compress_image(self.loaded_file_path)
            h, w = comp_data["dimensions"]
            orig_size = h * w
            entropy = self.lzw_l2.calculate_entropy(img.flatten())
            l1 = len(comp_data["codes"])
            bit_data = encode_progressive(comp_data["codes"], 256, 16)
            compressed_data = comp_data
        elif level == 3:
            comp_data, img = self.lzw_l3.compress(self.loaded_file_path)
            h, w = comp_data["dimensions"]
            orig_size = h * w
            entropy = self.lzw_l3.calculate_entropy(
                self.lzw_l3.compute_difference_image(img).flatten())
            l1 = len(comp_data["codes"])
            bit_data = encode_progressive(comp_data["codes"], 512, 16)
            compressed_data = comp_data
        elif level == 4:
            comp_data, img = self.lzw_l4.compress(self.loaded_file_path)
            h, w = comp_data["dimensions"]
            orig_size = h * w * 3
            entropy = sum(self.lzw_l4.calculate_entropy(cv2.split(img)[i].flatten())
                          for i in range(3)) / 3
            l1, l2, l3 = len(comp_data["B"]), len(comp_data["G"]), len(comp_data["R"])
            bit_data = (encode_progressive(comp_data["B"], 256, 16) +
                        encode_progressive(comp_data["G"], 256, 16) +
                        encode_progressive(comp_data["R"], 256, 16))
            compressed_data = comp_data
        elif level == 5:
            comp_data, img = self.lzw_l5.compress(self.loaded_file_path)
            h, w = comp_data["dimensions"]
            orig_size = h * w * 3
            entropy = sum(self.lzw_l5.calculate_entropy(
                self.lzw_l5.compute_difference_image(cv2.split(img)[i]).flatten())
                for i in range(3)) / 3
            l1, l2, l3 = len(comp_data["B"]), len(comp_data["G"]), len(comp_data["R"])
            bit_data = (encode_progressive(comp_data["B"], 512, 16) +
                        encode_progressive(comp_data["G"], 512, 16) +
                        encode_progressive(comp_data["R"], 512, 16))
            compressed_data = comp_data
        else:
            raise ValueError(f"Unknown level: {level}")

        header = [level, 16, h, w, l1, l2, l3]
        full_bits = header_to_binary_string(header) + bit_data
        padded = pad_encoded_text(full_bits)
        compressed_bytes = get_byte_array(padded)
        comp_size = len(compressed_bytes)

        cr = comp_size / orig_size if orig_size > 0 else 0.0
        cf = orig_size / comp_size if comp_size > 0 else 0.0
        ss = (orig_size - comp_size) / orig_size if orig_size > 0 else 0.0

        return {
            "compressed_data": compressed_data,
            "compressed_bytes": compressed_bytes,
            "orig_size": orig_size,
            "comp_size": comp_size,
            "entropy": entropy,
            "cr": cr, "cf": cf, "ss": ss,
        }

    def _on_compression_done(self, result: dict):
        self._set_busy(False)
        self.compressed_data = result["compressed_data"]
        self.compressed_bytes = result["compressed_bytes"]

        self.lbl_size_orig.setText(f"Original Size: {result['orig_size']:,} Byte")
        self.lbl_size_comp.setText(f"Compressed Size: {result['comp_size']:,} Byte")
        self.lbl_entropy.setText(f"Entropy: {result['entropy']:.4f} bit/pixel")
        self.lbl_cr.setText(
            f"CR: {result['cr']:.4f}  |  CF: {result['cf']:.4f}  |  SS: {result['ss']:.4f}")
        self.lbl_psnr.setText("PSNR: - | MSE: -  (calculated after decompression)")

        self.status_bar.showMessage(f"Level {self.current_level} compression completed.")
        QMessageBox.information(
            self, "Success",
            f"Level {self.current_level} compression completed.\n"
            f"Original: {result['orig_size']:,} B  →  Compressed: {result['comp_size']:,} B"
        )

    def save_compressed_file(self):
        if not self.compressed_bytes:
            QMessageBox.warning(self, "Warning", "No compressed data to save!")
            return
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed File", "",
            "LZW Binary (*.lzw);;All Files (*)"
        )
        if file_name:
            if not file_name.lower().endswith('.lzw'):
                file_name += '.lzw'
            with open(file_name, 'wb') as f:
                f.write(self.compressed_bytes)
            QMessageBox.information(self, "Success", f"Saved:\n{file_name}")

    def load_compressed_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Compressed .lzw File", "",
            "LZW Binary (*.lzw);;All Files (*)"
        )
        if not file_name:
            return
        try:
            with open(file_name, 'rb') as f:
                raw_bytes = f.read()

            bit_string = "".join(format(b, '08b') for b in raw_bytes)
            unpadded = remove_padding(bit_string)
            header = binary_string_to_header(unpadded[:7 * 16])

            level = header[0]
            max_cl = header[1]
            h, w = header[2], header[3]
            l1, l2, l3 = header[4], header[5], header[6]

            self.current_level = level
            data_bits = unpadded[7 * 16:]
            start_dict = 512 if level in (3, 5) else 256

            if level == 1:
                codes, _ = decode_progressive(data_bits, start_dict, max_cl, l1)
                self.compressed_data = codes
                self._show_text_mode()
            elif level in (2, 3):
                codes, _ = decode_progressive(data_bits, start_dict, max_cl, l1)
                self.compressed_data = {"dimensions": (h, w), "codes": codes}
                self._show_image_mode()
            elif level in (4, 5):
                b_codes, used_b = decode_progressive(data_bits, start_dict, max_cl, l1)
                g_codes, used_g = decode_progressive(data_bits[used_b:], start_dict, max_cl, l2)
                r_codes, _ = decode_progressive(data_bits[used_b + used_g:], start_dict, max_cl, l3)
                self.compressed_data = {
                    "dimensions": (h, w),
                    "B": b_codes, "G": g_codes, "R": r_codes
                }
                self._show_image_mode()
            else:
                raise ValueError(f"Unknown level: {level}")

            self.status_bar.showMessage(f"Compressed file loaded: Level {level}")
            QMessageBox.information(
                self, "Success",
                f"Level {level} LZW data loaded.\n"
                f"Dimensions: {w}x{h}  |  L1={l1}, L2={l2}, L3={l3}"
            )

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{exc}")

    def run_decompression(self):
        if self.compressed_data is None or self.current_level is None:
            QMessageBox.warning(self, "Warning", "No data to decompress!")
            return

        self._set_busy(True)
        data_copy = copy.deepcopy(self.compressed_data)

        self._worker = CompressionWorker(self._decompress_task, data_copy)
        self._worker.finished.connect(self._on_decompression_done)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _decompress_task(self, data_copy) -> dict:
        level = self.current_level
        result = {"level": level}

        if level == 1:
            result["text"] = self.lzw_l1.decompress(data_copy)
        elif level == 2:
            result["img"] = self.lzw_l2.decompress_image(data_copy)
        elif level == 3:
            result["img"] = self.lzw_l3.decompress(data_copy)
        elif level == 4:
            result["img"] = self.lzw_l4.decompress(data_copy)
        elif level == 5:
            result["img"] = self.lzw_l5.decompress(data_copy)

        return result

    def _on_decompression_done(self, result: dict):
        self._set_busy(False)
        level = result["level"]

        if level == 1:
            self.decompressed_text = result["text"]
            self.txt_decompressed.setText(self.decompressed_text)
            self.lbl_psnr.setText("PSNR: N/A (text)")
        else:
            self.decompressed_img = result["img"]
            self._display_image(self.decompressed_img, self.lbl_decompressed)

            if self.original_img is not None:
                orig_gray = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2GRAY) \
                    if self.decompressed_img.ndim == 2 and self.original_img.ndim == 3 \
                    else self.original_img
                mse, psnr = compute_psnr_mse(orig_gray, self.decompressed_img)
                if math.isinf(psnr):
                    psnr_str = "∞ (lossless)"
                else:
                    psnr_str = f"{psnr:.2f} dB"
                mse_str = f"{mse:.4f}" if not math.isnan(mse) else "N/A"
                self.lbl_psnr.setText(f"PSNR: {psnr_str}  |  MSE: {mse_str}")
            else:
                self.lbl_psnr.setText("PSNR: - (original not in memory)")

        self.status_bar.showMessage("Decompression completed.")
        QMessageBox.information(self, "Success", "Data successfully decompressed!")

    def save_restored_file(self):
        if self.current_level == 1 and self.decompressed_text is not None:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Decompressed Text", "restored_text.txt", "Text (*.txt)"
            )
            if file_name:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.decompressed_text)
                QMessageBox.information(self, "Success", f"Saved:\n{file_name}")

        elif self.current_level in (2, 3, 4, 5) and self.decompressed_img is not None:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Decompressed Image", "restored_image.png",
                "Image (*.png *.bmp)"
            )
            if file_name:
                cv2.imwrite(file_name, self.decompressed_img)
                QMessageBox.information(self, "Success", f"Saved:\n{file_name}")
        else:
            QMessageBox.warning(self, "Warning", "No decompressed data to save!")

    def _display_image(self, cv_img: np.ndarray, label_widget: QLabel):
        if cv_img.ndim == 2:
            h, w = cv_img.shape
            q_img = QImage(cv_img.copy().data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w = cv_img.shape[:2]
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb.copy().data, w, h, w * 3, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img)
        label_widget.setPixmap(
            pixmap.scaled(label_widget.width(), label_widget.height(), Qt.KeepAspectRatio,
                          Qt.SmoothTransformation)
        )

    def _show_text_mode(self):
        self.lbl_original.hide()
        self.txt_original.show()
        self.lbl_decompressed.hide()
        self.txt_decompressed.show()

    def _show_image_mode(self):
        self.txt_original.hide()
        self.lbl_original.show()
        self.txt_decompressed.hide()
        self.lbl_decompressed.show()

    def _reset_output_state(self):
        self.compressed_data = None
        self.compressed_bytes = None
        self.decompressed_img = None
        self.decompressed_text = None
        self.lbl_decompressed.clear()
        self.txt_decompressed.clear()

    def _set_busy(self, busy: bool):
        self.progress_bar.setVisible(busy)
        self.centralWidget().setEnabled(not busy)

    def _on_worker_error(self, message: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Error", f"Operation error:\n{message}")
        self.status_bar.showMessage("An error occurred.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LZWImageApp()
    window.show()
    sys.exit(app.exec_())