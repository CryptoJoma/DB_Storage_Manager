import configparser
import os
import requests
import time
from datetime import datetime
from tqdm import tqdm
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

# Ensure the backup directory exists
db_folder = config.get("db_folder")
os.makedirs(db_folder, exist_ok=True)

# API path
url_path = config.get("url_path")

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'
API_KEY = config.get("api_key")  # Add your API key here

# Authenticate Google Drive API
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Function to download the database with a progress bar
def download_db(dbname):
    db_url = f"{url_path}db_master_storage.php?dbname={dbname}"
    headers = {'X-API-KEY': API_KEY}

    try:
        response = requests.get(db_url, headers=headers, stream=True)
        response.raise_for_status()

        if response.status_code == 404:
            print("Error: 404 Not Found - Failed to create the backup file.")
            return None

        content_disposition = response.headers.get('Content-Disposition')
        if not content_disposition:
            print("Error: Content-Disposition header is missing.")
            return None
        
        filename = content_disposition.split('filename=')[1].strip('"')
        db_filename = os.path.join(db_folder, filename)

        total_size = int(response.headers.get('content-length', 0))
        with open(db_filename, "wb") as db_file, tqdm(
            desc=db_filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                db_file.write(data)
                bar.update(len(data))
        
        print(f"Database downloaded and saved as {db_filename}")
        upload_to_drive(db_filename, filename)
        return db_filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the database: {e}")
        return None

# Function to upload the file to Google Drive with a progress bar
def upload_to_drive(file_path, file_name):
    print(f"Connecting to Google")
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    folder_id = config.get("folder_id")
    file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
    media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)

    try:
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = None
        print(f"Uploading to Drive")

        with tqdm(total=os.path.getsize(file_path), unit='B', unit_scale=True, unit_divisor=1024, desc=f'Uploading {file_name}') as progress_bar:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress_bar.update(min(status.resumable_progress - progress_bar.n, os.path.getsize(file_path)))
        print(f"Upload completed")
    except Exception as e:
        print(f"Error during upload: {e}\n")

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f'Next run in: {timer}', end="\r")
        time.sleep(1)
        t -= 1

def main(interval):
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Running the scheduled task at {current_time}...")
        
        # List to store file paths for deletion
        files_to_delete = []
        
        # Read databases from CONFIG file
        with open("databases.txt", "r") as config_file:
            databases = [line.strip() for line in config_file if line.strip()]
        
        # Download and upload databases
        for db in databases:
            db_path = download_db(db)
            if db_path:
                files_to_delete.append(db_path)
        
        # Delete downloaded databases
        for file_path in files_to_delete:
            if file_path:
                os.remove(file_path)
                print(f"{os.path.basename(file_path)} deleted from local folder.")
        
        print(f"Task was completed. Bot will proceed to wait 3 days from now. \n")
        countdown(interval)

if __name__ == "__main__":
    print(f"Real-Time Bot: Scheduled Download DBs")
    print(f"The bot will check all databases every 3 days.\n")

    main(config.get("timer"))
