"""Places API (New) : client partagé, appelé uniquement par une commande autorisée."""
import time
import requests

MASK = ('places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,'
        'places.websiteUri,places.googleMapsUri,places.location,nextPageToken')


def search_places(query, key):
    results=[]
    token=None
    for page in range(3):
        payload={'textQuery':query,'pageSize':20,'languageCode':'fr'}
        if token:
            payload['pageToken']=token
        response=requests.post('https://places.googleapis.com/v1/places:searchText',
                               headers={'Content-Type':'application/json','X-Goog-Api-Key':key,'X-Goog-FieldMask':MASK},
                               json=payload,timeout=20)
        response.raise_for_status()
        data=response.json()
        if not isinstance(data,dict) or not isinstance(data.get('places',[]),list):
            raise ValueError('Réponse Places invalide.')
        results.extend(data.get('places',[]))
        token=data.get('nextPageToken')
        if not token:
            break
        time.sleep(1)
    return results
