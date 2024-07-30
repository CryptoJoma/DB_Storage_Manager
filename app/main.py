import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QFrame, QProgressBar, QToolButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon
from datetime import datetime
import logging
import time
import configparser
import os
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Function to read configuration from a file
def read_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

# Load configuration
config = read_config('config.ini')
theme = config["CONFIG"]["THEME"]

# Ensure the backup directory exists
db_folder = config["CONFIG"]["DB_FOLDER"]
os.makedirs(db_folder, exist_ok=True)

# Set timer
timer = int(config["CONFIG"]["TIMER"])

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'
API_KEY = config["CONFIG"]["API_KEY"]  # Add your API key here

# Authenticate Google Drive API
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.initial_pos = None

        # App Title Bar
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)
        
        # App icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon('icon.png').pixmap(32, 32))  # Load the icon
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setStyleSheet(
            """
        QLabel { border: none; }
        """
        )
        title_bar_layout.addWidget(self.icon_label)

        # Title Section
        self.title = QLabel(f"{self.__class__.__name__}", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
            """
        QLabel { text-transform: uppercase; font-size: 10pt; margin-left: 48px; border: none; }
        """
        )

        if title := parent.windowTitle():
            self.title.setText(title)
        title_bar_layout.addWidget(self.title)
        
        # Buttons Bar
        # Min button
        self.minimize_button = QToolButton(self)
        minimize_icon = QIcon()
        minimize_icon.addFile(f"themes/{theme}/images/min.svg")
        self.minimize_button.setIcon(minimize_icon)
        self.minimize_button.clicked.connect(self.minimize_window)

        # Normal button
        self.normal_button = QToolButton(self)
        normal_icon = QIcon()
        normal_icon.addFile(f"themes/{theme}/images/normal.svg")
        self.normal_button.setIcon(normal_icon)
        self.normal_button.clicked.connect(self.maximize_window)
        self.normal_button.setVisible(False)

        # Max button
        self.maximize_button = QToolButton(self)
        maximize_icon = QIcon()
        maximize_icon.addFile(f"themes/{theme}/images/max.svg")
        self.maximize_button.setIcon(maximize_icon)
        self.maximize_button.clicked.connect(self.maximize_window)

        # Close button
        self.close_button = QToolButton(self)
        close_icon = QIcon()
        close_icon.addFile(f"themes/{theme}/images/close.svg")
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.close_window)

        # Add buttons
        buttons = [
            self.minimize_button,
            self.normal_button,
            self.maximize_button,
            self.close_button,
        ]
        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(16, 16))
            button.setStyleSheet(
                """QToolButton {
                    border: none;
                    padding: 2px;
                }
                """
            )
            title_bar_layout.addWidget(button)

    def minimize_window(self):
        self.window().showMinimized()

    def maximize_window(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.normal_button.setVisible(True)
            self.maximize_button.setVisible(False)
        else:
            self.window().showMaximized()
            self.normal_button.setVisible(False)
            self.maximize_button.setVisible(True)

    def close_window(self):
        self.window().close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.initial_pos = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.initial_pos is not None:
            self.window().move(event.globalPos() - self.initial_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_window()
            event.accept()

class WorkerThread(QThread):
    update_log = pyqtSignal(str)
    update_timer = pyqtSignal(str)
    enable_button = pyqtSignal()
    update_progress = pyqtSignal(int)

    def __init__(self, interval_minutes):
        super().__init__()
        self.interval_minutes = interval_minutes
        self.setup_logging()

    def setup_logging(self):
        self.logger_db_downloader = logging.getLogger('db_downloader')
        handler_db_downloader = SignalHandler(self.update_log)
        self.logger_db_downloader.addHandler(handler_db_downloader)
        self.logger_db_downloader.setLevel(logging.DEBUG)

    # Function to download the database with a progress bar
    def download_db(self, dbname):
        headers = {'X-API-KEY': API_KEY}

        try:
            response = requests.get(dbname, headers=headers, stream=True)
            response.raise_for_status()

            if response.status_code == 404:
                self.update_log.emit("<span style=\"color: red;\">Error:</span> 404 Not Found - Failed to create the backup file.<br>")
                return None

            content_disposition = response.headers.get('Content-Disposition')
            if not content_disposition:
                self.update_log.emit("<span style=\"color: red;\">Error:</span> Content-Disposition header is missing.<br>")
                return None
            
            filename = content_disposition.split('filename=')[1].strip('"')
            db_filename = os.path.join(db_folder, filename)

            total_size = int(response.headers.get('Content-Length', 0))
            if total_size == 0:
                self.update_log.emit("<span style=\"color: yellow;\">Warning:</span> Content-Length is zero or missing; progress may not be accurate.<br>")
            
            downloaded_size = 0
            with open(db_filename, "wb") as db_file:
                for data in response.iter_content(chunk_size=1024):
                    db_file.write(data)
                    downloaded_size += len(data)
                    if total_size > 0:
                        self.update_progress.emit(int(downloaded_size / total_size * 100))
            
            self.update_log.emit(f"<span style=\"color: green;\">Success:</span> Database downloaded and saved as {db_filename}<br>")
            self.upload_to_drive(db_filename, filename)
            return db_filename
        except requests.exceptions.RequestException as e:
            self.update_log.emit(f"<span style=\"color: red;\">Error downloading the database:</span> {e}<br>")
            return None
        
    # Function to upload the file to Google Drive with a progress bar
    def upload_to_drive(self, file_path, file_name):
        self.update_log.emit(f"Connecting to Google")
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        folder_id = config["CONFIG"]["FOLDER_ID"]
        file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)

        try:
            request = service.files().create(body=file_metadata, media_body=media, fields='id')
            response = None
            self.update_log.emit(f"Uploading to Drive")

            total_size = os.path.getsize(file_path)
            while response is None:
                status, response = request.next_chunk()
                if status:
                    self.update_progress.emit(int(status.resumable_progress / total_size * 100))
            self.update_log.emit(f"<span style=\"color: green;\">Success:</span> Upload completed<br>")
        except Exception as e:
            self.update_log.emit(f"<span style=\"color: red;\">Error during upload:</span> {e}<br>")

    def countdown(self, t):
        while t:
            mins, secs = divmod(t, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            self.update_timer.emit(f'Next run in: {timer}')
            time.sleep(1)
            t -= 1

    def run(self):
        interval_seconds = self.interval_minutes * 60
        try:
            while True:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_log.emit(f"Running the scheduled task at {current_time}...\n")

                # List to store file paths for deletion
                files_to_delete = []
                
                # Read databases from CONFIG file
                with open("databases.txt", "r") as config_file:
                    databases = [line.strip() for line in config_file if line.strip()]
                
                # Download and upload databases
                for db in databases:
                    db_name = db.split("?dbname=")[1]
                    self.update_log.emit(f"<span style=\"color: yellow;\">===========</span> {db_name} <span style=\"color: yellow;\">===========</span>")
                    self.update_log.emit(f"\nConnecting to DB...")
                    db_path = self.download_db(db)
                    if db_path:
                        # Delete downloaded databases
                        os.remove(db_path)
                        self.update_log.emit(f"<span style=\"color: green;\">Success:</span> {os.path.basename(db_path)} deleted from local folder.<br>")

                self.update_log.emit(f"<span style=\"color: yellow;\">======================</span>")
                self.update_log.emit(f"\nTask was completed. Bot will proceed to wait 3 days from now.\n")
                self.countdown(interval_seconds)
        except Exception as e:
            self.update_log.emit(f"<span style=\"color: red;\">Error:</span> {str(e)}<br>")
            self.enable_button.emit()

class SignalHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("DB - Storage Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(open(f"themes/{theme}/style.qss", "r").read())  # Load the PyDracula stylesheet  
        self.setWindowIcon(QIcon('icon.png'))  

        self.custom_title_bar = CustomTitleBar(self)
        self.setMenuWidget(self.custom_title_bar)  

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)

        # Top frame for the timer
        self.top_frame = QFrame()
        self.top_frame.setFrameShape(QFrame.StyledPanel)
        self.top_frame.setFrameShadow(QFrame.Raised)
        self.top_layout = QHBoxLayout(self.top_frame)
        self.timer_label = QLabel("Next run in: 00:00")
        self.top_layout.addWidget(self.timer_label)
        self.layout.addWidget(self.top_frame)

        # Progress bar
        self.progress_bar_frame = QFrame()
        self.progress_bar_frame.setFrameShape(QFrame.StyledPanel)
        self.progress_bar_frame.setFrameShadow(QFrame.Raised)
        self.progress_bar_layout = QHBoxLayout(self.progress_bar_frame)
        self.progress_bar = QProgressBar()
        self.progress_bar_layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.progress_bar_frame)

        # Log output text box
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)
        
        # Bottom frame for the run button
        self.bottom_frame = QFrame()
        self.bottom_frame.setFrameShape(QFrame.StyledPanel)
        self.bottom_frame.setFrameShadow(QFrame.Raised)
        self.bottom_layout = QHBoxLayout(self.bottom_frame)
        self.run_button = QPushButton("Run Now")
        self.run_button.clicked.connect(self.start_tasks)
        self.bottom_layout.addWidget(self.run_button)
        self.layout.addWidget(self.bottom_frame)
        
        self.worker_thread = WorkerThread(timer) # TIMER: Minutes
        self.worker_thread.update_log.connect(self.update_log)
        self.worker_thread.update_timer.connect(self.update_timer)
        self.worker_thread.update_progress.connect(self.update_progress)
        self.worker_thread.enable_button.connect(self.enable_button)

    def start_tasks(self):
        self.run_button.setEnabled(False)
        self.worker_thread.start()

    def update_log(self, message):
        self.log_output.append(message)
    
    def update_timer(self, timer_message):
        self.timer_label.setText(timer_message)
    
    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def enable_button(self):
        self.run_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
