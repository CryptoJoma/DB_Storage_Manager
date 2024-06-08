import os
import requests
import time
from datetime import datetime

# Directory to store the downloaded databases
db_folder = "dbs"

# Ensure the backup directory exists
os.makedirs(db_folder, exist_ok=True)

# Function to download the database
def download_db(dbname):
    # URL of the PHP script that generates the database dump
    db_url = f"your/path/to/db_master_storage.php?dbname={dbname}"

    try:
        response = requests.get(db_url)
        response.raise_for_status()

        # Check for a 404 error
        if response.status_code == 404:
            print("Error: 404 Not Found - Failed to create the backup file.")
            return

        # Extract the filename from the Content-Disposition header
        content_disposition = response.headers.get('Content-Disposition')
        if not content_disposition:
            print("Error: Content-Disposition header is missing.")
            return
        
        filename = content_disposition.split('filename=')[1].strip('"')
        
        # Save the downloaded database file
        db_filename = os.path.join(db_folder, filename)
        with open(db_filename, "wb") as db_file:
            db_file.write(response.content)
        
        print(f"Database downloaded and saved as {db_filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the database: {e}")

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f'Next run in: {timer}', end="\r")
        time.sleep(1)
        t -= 1

def main(interval):

    while True:
        # Get the current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Running the scheduled task at {current_time}...")
        print(f"===========Title of your DB===========")
        print(f"Getting access to the DB")
        download_db("DBNAME_HERE")         # Download the database
        print(f"======================")
        print(f"Task was completed. Bot will proceed to wait 3 days from now. \n")
        # Show countdown timer
        countdown(interval)

# Initial download app
if __name__ == "__main__":

    print(f"Real-Time Bot: Scheduled Download DBs")
    print(f"The bot will check all databases every 3 days.\n")

    # Set the interval to 3 days (in seconds)
    interval = 3 * 24 * 60 * 60  # 3 days in seconds

    main(interval) # Run MainApp
