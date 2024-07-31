# DB_Storage_Manager
It is a Python application built with PyQt5. It allows users to securely download databases from a PHP API using an API key and upload them to Google Drive. The application provides a user-friendly interface with progress bars and logging functionality. It utilizes Google Drive API and OAuth 2.0 for secure authentication and file upload. This project demonstrates an integration of PyQt5 with web APIs and cloud services for database management.

# Features
- Database Download: Allows users to download databases from a PHP API securely.
- Google Drive Upload: Enables users to upload downloaded databases to Google Drive for safe storage.
- User-friendly Interface: Provides a graphical user interface (GUI) built with PyQt5, making it easy for users to interact with the application.
- Progress Tracking: Displays progress bars for both download and upload processes, allowing users to track the progress of each task.
- Logging: Logs the status of each task, providing users with detailed information about the download and upload operations.
- Secure Authentication: Utilizes API keys and OAuth 2.0 for secure authentication when accessing the PHP API and Google Drive API, ensuring data security.
- Error Handling: Handles errors gracefully and provides informative messages to users in case of download or upload failures.
- Customization: Allows users to customize the behavior of the application by configuring API keys, credentials, and other parameters in the source code.
- Simple Configuration: Easily specify the database names to download.
- Countdown Timer: Displays a countdown until the next scheduled download.
- Automated Downloads: Downloads database backups every X days.

# Installation
1. Clone the repository to your local machine:
```rb
git clone https://github.com/CryptoJoma/db-storage-manager.git
```
2. Install the required Python packages:
```rb
pip install -r requirements.txt
```
3. Place your Google Drive service account credentials in a file named credentials.json in the project directory.
4. Add your API information to the variable in config.ini

# Usage
1. Run the script:
```rb
python main.py
```
2. Enter the database name in the provided input field.
3. Click the "Start" button to initiate the download and upload process.
4. The progress bars will indicate the progress of the download and upload processes.
5. Upon completion, the log will display the status of the tasks.

# Dependencies
- Python 3.x
- PyQt5
- requests
- google-auth
- google-api-python-client
- tqdm
- configparser

Ensure the script can access the required URL and the "DBs" folder is writable. The script will automatically create the "DBs" folder if it does not exist.
