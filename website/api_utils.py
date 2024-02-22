from dotenv import load_dotenv
import os
import requests

def get_access_token():
    ''' collects the access token'''
    load_dotenv()
    refresh_token = os.getenv('refresh_token')

    # Get Access token
    headers = {'Authorization': f'Bearer {refresh_token}'}
    auth_response = requests.get('https://cloud.hawkindynamics.com/api/token', headers=headers)
    auth_response.raise_for_status()  
    return (auth_response.json().get('access_token'))


def get_athlete_data(hawkin_api_id):
    ''' Collect the data from an individual athlete'''

    access_token = get_access_token()

    url = f'https://cloud.hawkindynamics.com/api/colby?athleteId={hawkin_api_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    test  = requests.get(url, headers=headers)

    return(test.json())
    
def parse_jump_data(data, db):
    '''Parse the data form the API and sets it to a more manage format'''

    data = data['data']
    clean_data = [['hawking-id'],['Timestamp'],['Jump Height'],['Braking RFD'],['Peak Propulsive Force'],['mRSI']]

    for jump in data:

        athlete_id = jump['athlete']['id']
        timestamp = jump['timestamp']
        jh = jump['Jump Height(m)']
        rfd = jump['Braking RFD(N/s)']
        ppf = jump['Peak Propulsive Force(N)']
        mrsi = jump['mRSI']

    return(clean_data)







