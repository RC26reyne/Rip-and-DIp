import sys
import subprocess
import re
import os
import time
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, 
    QTextEdit, QFrame, QProgressBar, QPlainTextEdit,
    QTabWidget, QListWidget, QSplashScreen
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QMouseEvent, QDragEnterEvent, QDropEvent, QPixmap, QPainter, QColor

# --- WORKER 1: DOWNLOADER ---
class BatchDownloadWorker(QThread):
    progress_signal = Signal(int)
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, urls, base_cmd_flags, output_dir):
        super().__init__()
        self.urls = urls
        self.base_flags = base_cmd_flags
        self.output_dir = output_dir

    def run(self):
        total_files = len(self.urls)
        for index, url in enumerate(self.urls):
            current_num = index + 1
            self.log_signal.emit(f"\n>> ENGAGING TARGET {current_num}/{total_files}...\n>> URL: {url}")
            self.progress_signal.emit(0)

            cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist"] + self.base_flags
            if self.output_dir:
                cmd += ["-o", f"{self.output_dir}/%(title)s.%(ext)s"]
            cmd.append(url)

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace'
            )
            percent_pattern = re.compile(r"(\d{1,3}\.\d)%")

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    clean_line = line.strip()
                    if "[download]" not in clean_line or "%" not in clean_line:
                        self.log_signal.emit(clean_line)
                    if "[download]" in clean_line and "%" in clean_line:
                        match = percent_pattern.search(clean_line)
                        if match:
                            try:
                                val = int(float(match.group(1)))
                                self.progress_signal.emit(val)
                            except ValueError:
                                pass
            self.progress_signal.emit(100)
            self.log_signal.emit(f">> TARGET {current_num} NEUTRALIZED.")

        self.finished_signal.emit()

# --- WORKER 2: BATCH DIP (STEM SEPARATOR) ---
class BatchStemWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, file_paths, output_dir):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir

    def run(self):
        total = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths):
            self.log_signal.emit(f"\n>> PROCESSING FILE {i+1}/{total}...\n>> TARGET: {os.path.basename(file_path)}")
            self.progress_signal.emit(0) 

            cmd = ["audio-separator", "--model_filename", "htdemucs_ft.yaml"]
            if self.output_dir:
                cmd += ["--output_dir", self.output_dir]
            cmd.append(file_path)
                
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace'
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log_signal.emit(line.strip())
            
            self.log_signal.emit(f">> FILE {i+1} COMPLETED.")
        
        self.finished_signal.emit()


# --- MAIN WINDOW ---
class RipAndDip(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.95)
        self.resize(800, 720)
        self.setAcceptDrops(True)
        self.old_pos = None
        self.dl_output_dir = ""
        self.stem_output_dir = ""
        self.stem_input_files = [] 
        self.setup_ui()
        self.apply_styles()
        self.log.append(">> SYSTEM BOOT SEQUENCE INITIATED...")
        self.log.append(">> PYTHON 3.10 ENVIRONMENT DETECTED.")
        self.log.append(">> BATCH PROTOCOLS ACTIVE.")

    def setup_ui(self):
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        master_layout.addWidget(self.main_frame)
        layout = QVBoxLayout(self.main_frame)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 35, 40, 40)

        # Title Bar
        title_bar = QHBoxLayout()
        self.title_label = QLabel("RIP AND DIP // STUDIO_EDITION")
        self.min_btn = QPushButton("_")
        self.min_btn.setFixedSize(25, 25)
        self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.clicked.connect(self.close)
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()
        title_bar.addWidget(self.min_btn)
        title_bar.addWidget(self.close_btn)
        layout.addLayout(title_bar)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tab_rip = QWidget()
        self.setup_rip_tab()
        self.tabs.addTab(self.tab_rip, " [ PROTOCOL: RIP ] ")
        self.tab_dip = QWidget()
        self.setup_dip_tab()
        self.tabs.addTab(self.tab_dip, " [ PROTOCOL: DIP ] ") 

        # Logs
        self.log_label = QLabel("SYSTEM_LOG:")
        layout.addWidget(self.log_label)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        layout.addWidget(self.log)

    def setup_rip_tab(self):
        layout = QVBoxLayout(self.tab_rip)
        layout.setSpacing(15)
        lbl = QLabel("TARGET_LIST (DRAG LINKS HERE):")
        layout.addWidget(lbl)
        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(">> PASTE URLs OR DRAG LINKS HERE")
        layout.addWidget(self.url_input)
        fmt_row = QHBoxLayout()
        fmt_label = QLabel("FORMAT:")
        self.format_box = QComboBox()
        self.format_box.addItems(["WAV", "MP3", "AAC", "MP4"])
        fmt_row.addWidget(fmt_label)
        fmt_row.addWidget(self.format_box)
        layout.addLayout(fmt_row)
        self.dl_progress = QProgressBar()
        self.dl_progress.setValue(0)
        self.dl_progress.setFormat("%p% DOWNLOADING")
        layout.addWidget(self.dl_progress)
        btn_row = QHBoxLayout()
        self.dl_folder_btn = QPushButton("OUTPUT DIR")
        self.dl_folder_btn.clicked.connect(self.choose_dl_folder)
        self.dl_btn = QPushButton("INITIATE DOWNLOAD")
        self.dl_btn.clicked.connect(self.start_download)
        btn_row.addWidget(self.dl_folder_btn)
        btn_row.addWidget(self.dl_btn)
        layout.addLayout(btn_row)

    def setup_dip_tab(self):
        layout = QVBoxLayout(self.tab_dip)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)
        info = QLabel(">> BATCH SEPARATION // NEURAL NET: HTDEMUCS")
        info.setStyleSheet("color: #00ff41; border: none;")
        layout.addWidget(info)
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("border: 1px solid #005f73; color: #00f0ff; background: #050505;")
        self.file_list.setMaximumHeight(150)
        layout.addWidget(self.file_list)
        pick_btn = QPushButton("ADD SOURCE AUDIO FILES")
        pick_btn.clicked.connect(self.choose_source_files)
        layout.addWidget(pick_btn)
        clr_btn = QPushButton("CLEAR LIST")
        clr_btn.clicked.connect(self.clear_dip_list)
        layout.addWidget(clr_btn)
        self.stem_out_label = QLabel("OUTPUT: [DEFAULT FOLDER]")
        layout.addWidget(self.stem_out_label)
        out_btn = QPushButton("SELECT OUTPUT FOLDER (OPTIONAL)")
        out_btn.clicked.connect(self.choose_stem_folder)
        layout.addWidget(out_btn)
        layout.addStretch()
        self.split_btn = QPushButton("EXECUTE DIP PROTOCOL")
        self.split_btn.clicked.connect(self.start_split)
        self.split_btn.setStyleSheet("border: 1px solid #ff003c; color: #ff003c;")
        layout.addWidget(self.split_btn)
        self.stem_progress = QProgressBar()
        self.stem_progress.setRange(0, 0)
        self.stem_progress.setTextVisible(False)
        self.stem_progress.hide()
        layout.addWidget(self.stem_progress)

    def apply_styles(self):
        border_css = ""
        if os.path.exists("border.png"):
            border_css = """
                border-image: url(border.png) 50 stretch;
                border-width: 50px;
                background-color: #0a0a12; 
            """
        else:
            border_css = "border: 2px solid #00f0ff; background-color: #0a0a12;"

        style_sheet = f"""
            QFrame#MainFrame {{ {border_css} }}
            QWidget {{
                color: #00f0ff;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 13px;
                background: transparent; 
            }}
            QTabWidget::pane {{ border: 1px solid #005f73; background: #000000; }}
            QTabBar::tab {{
                background: #0a0a12;
                border: 1px solid #005f73;
                padding: 10px;
                margin-right: 2px;
                color: #005f73;
            }}
            QTabBar::tab:selected {{
                background: #00f0ff;
                color: #000000;
                font-weight: bold;
            }}
            QLabel {{ font-weight: bold; color: #00f0ff; }}
            QPlainTextEdit, QComboBox, QTextEdit {{
                background-color: #050505;
                border: 1px solid #005f73;
                padding: 6px;
                color: #00f0ff;
            }}
            QPushButton {{
                background-color: #0a0a12;
                border: 1px solid #00f0ff;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #00f0ff; color: #000000; }}
            QPushButton#CloseBtn:hover {{ background-color: #ff003c; border: 1px solid #ff003c; color: white; }}
            QTextEdit {{ color: #00ff41; font-size: 11px; }}
            QScrollBar:vertical {{ border: none; background: #0a0a12; width: 10px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: #005f73; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """
        self.setStyleSheet(style_sheet)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if urls[0].isLocalFile():
                self.tabs.setCurrentIndex(1)
                count = 0
                for u in urls:
                    f_path = u.toLocalFile()
                    if f_path.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
                        self.stem_input_files.append(f_path)
                        self.file_list.addItem(os.path.basename(f_path))
                        count += 1
                if count > 0: self.log.append(f">> DROP DETECTED: {count} AUDIO FILES ADDED.")
            else:
                self.tabs.setCurrentIndex(0)
                for u in urls:
                    self.url_input.appendPlainText(u.toString())
                self.log.append(">> DROP DETECTED: URLS ADDED.")
        elif mime.hasText():
            text = mime.text().strip()
            if text.startswith("http"):
                self.tabs.setCurrentIndex(0)
                self.url_input.appendPlainText(text)
        event.acceptProposedAction()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    def choose_dl_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Output Folder")
        if folder:
            self.dl_output_dir = folder
            self.log.append(f">> DOWNLOAD DIR SET: {folder}")

    def start_download(self):
        raw_text = self.url_input.toPlainText()
        urls = [line.strip() for line in raw_text.split('\n') if line.strip()]
        if not urls:
            self.log.append("!! ERROR: NO TARGETS !!")
            return
        selection = self.format_box.currentText()
        base_flags = []
        if "WAV" in selection: base_flags += ["-x", "--audio-format", "wav"]
        elif "MP3" in selection: base_flags += ["-x", "--audio-format", "mp3"]
        elif "AAC" in selection: base_flags += ["-x", "--audio-format", "aac"]
        else: base_flags += ["-f", "bv*+ba", "--merge-output-format", "mp4"]
        self.dl_btn.setEnabled(False)
        self.dl_worker = BatchDownloadWorker(urls, base_flags, self.dl_output_dir)
        self.dl_worker.log_signal.connect(self.log.append)
        self.dl_worker.progress_signal.connect(self.dl_progress.setValue)
        self.dl_worker.finished_signal.connect(lambda: self.dl_btn.setEnabled(True))
        self.dl_worker.start()

    def choose_source_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", "Audio Files (*.mp3 *.wav *.flac *.m4a)")
        if files:
            for f in files:
                self.stem_input_files.append(f)
                self.file_list.addItem(os.path.basename(f))
            self.log.append(f">> ADDED {len(files)} FILES TO QUEUE.")

    def clear_dip_list(self):
        self.stem_input_files = []
        self.file_list.clear()
        self.log.append(">> QUEUE CLEARED.")

    def choose_stem_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Stem Output Folder")
        if folder:
            self.stem_output_dir = folder
            self.stem_out_label.setText(f"OUTPUT: {os.path.basename(folder)}")

    def start_split(self):
        if not self.stem_input_files:
            self.log.append("!! ERROR: NO FILES IN QUEUE !!")
            return
        self.split_btn.setEnabled(False)
        self.stem_progress.show()
        self.log.append(f">> INITIATING BATCH DIP PROTOCOL ON {len(self.stem_input_files)} FILES...")
        self.stem_worker = BatchStemWorker(self.stem_input_files, self.stem_output_dir)
        self.stem_worker.log_signal.connect(self.log.append)
        self.stem_worker.finished_signal.connect(self.split_finished)
        self.stem_worker.start()

    def split_finished(self):
        self.split_btn.setEnabled(True)
        self.stem_progress.hide()
        self.log.append(">> BATCH DIP COMPLETE. ALL STEMS SECURED.")

# --- SPLASH SCREEN GENERATOR ---
def create_base_splash():
    pixmap = QPixmap(600, 300)
    pixmap.fill(QColor(10, 10, 18))
    painter = QPainter(pixmap)
    # Border
    painter.setPen(QColor(0, 240, 255))
    painter.drawRect(0, 0, 599, 299)
    painter.drawRect(5, 5, 589, 289)
    # Title
    font = QFont("Consolas", 28)
    font.setStyleStrategy(QFont.NoAntialias)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(0, 240, 255))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "RIP AND DIP\nSTUDIO EDITION")
    painter.end()
    return pixmap

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Consolas")
    font.setStyleHint(QFont.Monospace)
    app.setFont(font)

    # 1. Create Base Image
    base_pix = create_base_splash()
    splash = QSplashScreen(base_pix, Qt.WindowStaysOnTopHint)
    splash.show()

    # 2. Fake Loading Loop (5 Seconds)
    loading_texts = [
        "INITIALIZING CORE...", 
        "LOADING NEURAL NETWORKS...", 
        "CALIBRATING FLUX CAPACITORS...",
        "CONNECTING TO THE VOID...",
        "DECRYPTING ALGORITHMS...",
        "SYSTEM READY."
    ]

    # Run 100 steps
    for i in range(101):
        # Copy base so we don't draw over previous frames permanently
        frame = base_pix.copy()
        painter = QPainter(frame)
        
        # Draw Progress Bar Container
        painter.setPen(QColor(0, 95, 115))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(50, 250, 500, 20)
        
        # Draw Cyan Bar inside
        bar_width = int(500 * (i / 100.0))
        painter.setBrush(QColor(0, 240, 255)) # Cyan fill
        painter.setPen(Qt.NoPen)
        if bar_width > 0:
            painter.drawRect(50, 250, bar_width, 20)

        # Draw Loading Text
        text_idx = min(i // 20, len(loading_texts) - 1)
        txt = loading_texts[text_idx]
        
        font_small = QFont("Consolas", 10)
        painter.setFont(font_small)
        painter.setPen(QColor(0, 240, 255))
        painter.drawText(50, 240, f"{txt} [{i}%]")

        painter.end()
        
        splash.setPixmap(frame)
        app.processEvents() # Force UI update
        time.sleep(0.05) # 0.05s * 100 = 5 seconds

    win = RipAndDip()
    win.show()
    splash.finish(win)
    sys.exit(app.exec())