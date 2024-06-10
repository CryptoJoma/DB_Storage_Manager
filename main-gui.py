import configparser
import os
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QWidget, QTextEdit, QProgressBar, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt  # Import Qt from PyQt5.QtCore
from PyQt5.QtGui import QPainter  # Import QPainter from PyQt5.QtGui
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Function to read configuration from a file
def read_config(file_path):
    config = {}
    parser = configparser.ConfigParser()
    parser.read(file_path)
    for section in parser.sections():
        for key, value in parser.items(section):
            config[key] = value
    return config

# Load configuration
config = read_config('config.ini')

# Directory to store the downloaded databases
db_folder = config.get("db_folder")
os.makedirs(db_folder, exist_ok=True)

# API path
url_path = config.get("url_path")

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'
API_KEY = config.get("api_key")  # Add your API key here

class Worker(QThread):
    log_signal = pyqtSignal(str)
    download_progress_signal = pyqtSignal(int)
    upload_progress_signal = pyqtSignal(int)

    def __init__(self, dbname):
        super().__init__()
        self.dbname = dbname

    def run(self):
        self.log_signal.emit("Getting access to the DB")
        db_filename = self.download_db(self.dbname)
        if db_filename:
            self.upload_to_drive(db_filename)
            os.remove(db_filename)
            self.log_signal.emit(f"{os.path.basename(db_filename)} deleted from local folder")
        self.log_signal.emit("======================\n")

    def download_db(self, dbname):
        db_url = f"{url_path}db_master_storage.php?dbname={dbname}"
        headers = {'X-API-KEY': API_KEY}
        try:
            response = requests.get(db_url, headers=headers, stream=True)
            response.raise_for_status()
            if response.status_code == 404:
                self.log_signal.emit("Error: 404 Not Found - Failed to create the backup file")
                return None

            content_disposition = response.headers.get('Content-Disposition')
            if not content_disposition:
                self.log_signal.emit("Error: Content-Disposition header is missing")
                return None

            filename = content_disposition.split('filename=')[1].strip('"')
            db_filename = os.path.join(db_folder, filename)

            total_length = response.headers.get('content-length')
            if total_length is None:
                with open(db_filename, "wb") as db_file:
                    db_file.write(response.content)
            else:
                total_length = int(total_length)
                with open(db_filename, "wb") as db_file:
                    downloaded = 0
                    for data in response.iter_content(chunk_size=4096):
                        downloaded += len(data)
                        db_file.write(data)
                        done = int(100 * downloaded / total_length)
                        self.download_progress_signal.emit(done)

            self.log_signal.emit(f"Database downloaded and saved as {db_filename}")
            return db_filename
        except requests.exceptions.RequestException as e:
            self.log_signal.emit(f"Error downloading the database: {e}\n")
            return None

    def upload_to_drive(self, file_path):
        self.log_signal.emit("Connecting to Google")
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        folder_id = config.get("folder_id")
        file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)

        try:
            request = service.files().create(body=file_metadata, media_body=media, fields='id')
            response = None
            self.log_signal.emit("Uploading to Drive")

            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.upload_progress_signal.emit(progress)

            self.upload_progress_signal.emit(100)
            self.log_signal.emit("Upload completed")
        except Exception as e:
            self.log_signal.emit(f"Error during upload: {e}\n")

class ProgressBarWithText(QProgressBar):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        rect = self.rect()
        painter.drawText(rect, Qt.AlignCenter, self.text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DB Storage Manager")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.dbname_label = QLabel("Database Name:")
        self.dbname_input = QLineEdit()

        # Create a horizontal layout for the input field and the start button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.dbname_label)
        input_layout.addWidget(self.dbname_input)

        # Store the Start button as an instance variable
        self.start_button = QPushButton("Start")
        input_layout.addWidget(self.start_button)  # Add the start button to the input layout

        self.download_progress = ProgressBarWithText("Download")
        layout.addLayout(input_layout)  # Add the input layout to the main layout
        layout.addWidget(self.download_progress)

        self.upload_progress = ProgressBarWithText("Upload")
        layout.addWidget(self.upload_progress)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        container = QWidget()  # Create a container widget to hold the layout
        container.setLayout(layout)  # Set the main layout for the container
        self.setCentralWidget(container)  # Set the container as the central widget of QMainWindow

        # Connect the Start button's clicked signal to the start_task method
        self.start_button.clicked.connect(self.start_task)

    def start_task(self):
        dbname = self.dbname_input.text()

        self.worker = Worker(dbname)
        self.worker.log_signal.connect(self.update_log)
        self.worker.download_progress_signal.connect(self.update_download_progress)
        self.worker.upload_progress_signal.connect(self.update_upload_progress)
        self.worker.start()

    def update_log(self, message):
        self.log_text.append(message)

    def update_download_progress(self, value):
        self.download_progress.setValue(value)

    def update_upload_progress(self, value):
        self.upload_progress.setValue(value)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
