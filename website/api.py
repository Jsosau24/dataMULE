import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

configure()

refresh_token = os.getenv('refresh_token')

headers = {'Authorization': f'Bearer {refresh_token}'}
auth_response = requests.get('https://cloud.hawkindynamics.com/api/token', headers=headers)
auth_response.raise_for_status()  
access_token = auth_response.json().get('access_token')

# Calculate the Unix timestamp for the start of today
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
timestamp = int(time.mktime(today.timetuple()))

url = f'https://cloud.hawkindynamics.com/api/colby?from=1705968000'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'  # Explicitly accept JSON responses
}
test  = requests.get(url, headers=headers)
print(test.json())







