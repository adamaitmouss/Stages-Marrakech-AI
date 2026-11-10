import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import requests
import json

def main():
    prepare(external=True)
    API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {'Content-Type': 'application/json', 'X-Goog-Api-Key': API_KEY, 'X-Goog-FieldMask': 'places.displayName,places.formattedAddress'}
    data = {'textQuery': 'entreprises Marrakech'}
    response = requests.post(url, headers=headers, json=data, timeout=20)
    print('Code :', response.status_code)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
