import requests
from app.core.config import settings

class LocationService:
    def __init__(self):
        self.geonames_url = settings.GEONAMES_API_BASE_URL
        self.geonames_user = settings.GEONAMES_USERNAME
        if not self.geonames_user:
            print("CRITICAL ERROR: GEONAMES_USERNAME is not set in settings.")

    def _check_username(self):
        if not self.geonames_user:
            print("Error: GEONAMES_USERNAME is not configured in LocationService.")
            return False
        return True

    def get_geoname_id_country(self, country_name_or_code, lang='es'):
        if not self._check_username():
            return None

        params = {
            'q': country_name_or_code,
            'maxRows': 1,
            'featureClass': 'A',
            'featureCode': 'PCLI',
            'username': self.geonames_user,
            'type': 'json',
            'lang': lang
        }
        try:
            response = requests.get(f"{self.geonames_url}/searchJSON", params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('totalResultsCount', 0) > 0 and 'geonames' in data and data['geonames']:
                for item in data['geonames']:
                    if item.get('fcode') == 'PCLI':
                        return item.get('geonameId')
                print(f"Warning: No exact 'PCLI' found for '{country_name_or_code}'. Using the first result of class 'A'.")
                if data['geonames']:
                    return data['geonames'][0].get('geonameId')
                else:
                    print(f"No suitable geonameId found for the country: {country_name_or_code} despite results.")
                    return None
            else:
                print(f"No geonameId found for the country: {country_name_or_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error in the request to GeoNames (searchJSON): {e}")
            return None
        except ValueError:
            print(f"Error decoding the JSON response from GeoNames (searchJSON). Response: {response.text if 'response' in locals() else 'No response'}")
            return None

    def get_adm1_subdivisions_country(self, geoname_id_country, lang='es'):
        if not self._check_username() or not geoname_id_country:
            return None

        params = {
            'geonameId': geoname_id_country,
            'username': self.geonames_user,
            'lang': lang,
            'type': 'json'
        }
        try:
            response = requests.get(f"{self.geonames_url}/childrenJSON", params=params)
            response.raise_for_status()
            data = response.json()

            subdivisions = []
            if data.get('totalResultsCount', 0) > 0 and 'geonames' in data:
                for item in data['geonames']:
                    if item.get('fcode') == 'ADM1':
                        name_to_use = item.get('name')
                        toponym_name = item.get('toponymName')
                        
                        if not name_to_use or (name_to_use == toponym_name and toponym_name):
                             name_to_use = toponym_name if toponym_name else name_to_use

                        subdivisions.append({
                            'name': name_to_use,
                            'geonameId': item.get('geonameId')
                        })
                
                valid_subdivisions = [s for s in subdivisions if s.get('name')]
                return valid_subdivisions

            elif 'status' in data:
                print(f"GeoNames API error (childrenJSON): {data['status']['message']} (Value: {data['status'].get('value')})")
                return None
            else:
                print(f"No ADM1 subdivisions found for geonameId {geoname_id_country} or the response was unexpected.")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error in the request to GeoNames (childrenJSON): {e}")
            return None
        except ValueError:
            print(f"Error decoding the JSON response from GeoNames (childrenJSON). Response: {response.text if 'response' in locals() else 'No response'}")
            return None

    def get_subdivision_names_country(self, country_name_or_code, lang='es'):
        if not self._check_username():
            return None
            
        print(f"Searching ID for: {country_name_or_code} with lang: {lang}")
        geoname_id = self.get_geoname_id_country(country_name_or_code, lang=lang)
        if geoname_id:
            print(f"GeonameID found for {country_name_or_code}: {geoname_id}")
            subdivisions_data = self.get_adm1_subdivisions_country(geoname_id, lang=lang)
            
            if subdivisions_data is not None:
                return [subdiv['name'] for subdiv in subdivisions_data if subdiv.get('name')]
            else:
                return None
        else:
            return None

location_service = LocationService()
