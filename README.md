# DB_Master_Storage
This Python script automates the process of downloading database backups from a web server every X days. The script retrieves SQL dump files using a specified PHP endpoint, saving them to a local directory while retaining their original filenames. It runs continuously, ensuring your database backups are always up-to-date.

# Features
Automated Downloads: Downloads database backups every 3 days.
Retains Original Filenames: Extracts and saves files with their original names from the server.
Simple Configuration: Easily specify the database names to download.
Countdown Timer: Displays a countdown until the next scheduled download.

# Usage
1. Clone the repository: git clone https://github.com/CryptoJoma/DB_Master_Storage.git
2. Navigate to the Folder Project: cd DB_Master_Storage
3. Install required packages: pip install requests
4. Run the script: python main.py

Ensure the script has access to the required URL and that the "dbs" folder is writable. The script will automatically create the "dbs" folder if it does not exist.
