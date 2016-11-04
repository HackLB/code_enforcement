#!/usr/bin/env python
import os, re, sys
import requests
from pipes import quote
from bs4 import BeautifulSoup
from pprint import pprint
import simplejson as json
import urllib.parse

from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut


with open('../secrets.json') as f:    
    secrets = json.load(f)

geolocator = GoogleV3(api_key=secrets['google_api_key'])


url_template = 'http://sapphire.longbeach.gov/HPLandMgmt/CE/ActiveCodeEnforcementCases{}.asp'
districts = 9


def geocode(address):
    try:
        location = geolocator.geocode(address, timeout=2)
        if location:
            data = {"latitude": location.latitude, "longitude": location.longitude, "address": location.address}
            print(data)
            return data
        else:
            return None
    except GeocoderTimedOut:
        return geocode(address)


def cleanup(label):
    """
    Used for converting field names into form suitable for use
    as Python dictionary keys.
    """
    return label.lower().replace(' ','_').replace('.','').replace('#','num').replace(':','')

def scrape_records(district):
    """
    Extracts case records from the per-district Web pages,
    eg, http://sapphire.longbeach.gov/HPLandMgmt/CE/ActiveCodeEnforcementCases1.asp
    then puts each record into a dictionary with keys based on 
    field names, and returns a list of dictionaries
    """
    print('Getting code enforcement data for district {}...'.format(district))
    r = requests.get(url_template.format(district))
    soup = BeautifulSoup(r.content, 'html.parser')

    rows = soup.find('table').find_all('tr')
    records = []
    record = {'district': district}
    for row in rows[1:]:
        if len(row.find_all('hr')) == 1:
            records.append(record)
            record = {'district': district}
        else:
            cells = row.find_all('td')
            label = cleanup(cells[0].string)
            record[label] = cells[1].string

    records.append(record)
    return records


def save_records(records):
    """
    Saves records to invidual JSON files. Files are saved into a
    different directory for each city district, and are named based
    on the code enforcement case number.
    """
    print('Saving code enforcement data...')
    for record in records:
        district_path = os.path.join(data_path, str(record['district']))
        record_path = os.path.join(district_path, record['case_num'] + '.json')
        os.makedirs(district_path, exist_ok=True)

        with open(record_path, 'w') as f:
            json.dump(record, f, indent = 4, ensure_ascii=False, sort_keys = True)


def clean_records(records):
    """
    Saves records to invidual JSON files. Files are saved into a
    different directory for each city district, and are named based
    on the code enforcement case number.
    """
    print('Cleaning code enforcement data...')
    for record in records:
        address = '{}, Long Beach, CA'.format(record['address'])
        location = geocode(address)
        record['location'] = location
    return records


if __name__ == "__main__":
    repo_path = os.path.dirname(os.path.realpath(sys.argv[0])) # Path to current directory
    data_path = os.path.join(repo_path, '_data') # Root path for record data
    os.makedirs(data_path, exist_ok=True)

    for district in range(1, districts + 1): # Loop through districts 1 through...
        records = scrape_records(district)   # Scrape the records for each district...
        records = clean_records(records)   # Scrape the records for each district...
        save_records(records)                # Save the scraped records to JSON files...

