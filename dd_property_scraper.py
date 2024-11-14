from curl_cffi import requests
import time
import json
from typing import List, Dict
from bs4 import BeautifulSoup

class DDPropertyScraper:
    def __init__(self):
        # // Inicjalizacja podstawowych ustawień
        self.base_url = "https://www.ddproperty.com"
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.ddproperty.com/',
            'Origin': 'https://www.ddproperty.com',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.impersonate = "chrome110"

    def extract_listings_data(self, search_url: str) -> List[Dict]:
        """
        // Pobiera dane o ogłoszeniach z wyników wyszukiwania
        Args:
            search_url (str): URL z parametrami wyszukiwania
        Returns:
            List[Dict]: Lista ogłoszeń z wymaganymi danymi
        """
        try:
            # // Najpierw odwiedź stronę główną aby pobrać ciasteczka
            self.session.get(
                self.base_url,
                impersonate=self.impersonate
            )
            time.sleep(2)
            
            print(f"Making request to: {search_url}")
            response = self.session.get(
                search_url,
                impersonate=self.impersonate,
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script', {'type': 'text/javascript'})
            target_script = None
            
            for script in script_tags:
                if script.string and 'listingResultsWidget' in script.string:
                    target_script = script
                    break
                    
            if not target_script:
                print("Debug: Could not find script tag with listing data")
                return []

            script_content = target_script.string
            start_idx = script_content.find('var guruApp = ') + len('var guruApp = ')
            end_idx = script_content.find('};', start_idx) + 1
            
            if start_idx == -1 or end_idx == -1:
                print("Debug: Could not find proper JSON data markers")
                return []
                
            json_str = script_content[start_idx:end_idx]
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Debug: JSON parsing error: {str(e)}")
                print(f"Debug: JSON string start: {json_str[:200]}...")
                return []
            
            listings = []
            listings_data = data.get('listingResultsWidget', {}).get('gaECListings', [])
            listings_urls = data.get('listingResultsWidget', {}).get('listings', [])
            
            print(f"Debug: Found {len(listings_data)} listings")
            
            for i, listing in enumerate(listings_data):
                product_data = listing.get('productData', {})
                agent_data = listings_urls[i] if i < len(listings_urls) else {}
                
                url = agent_data.get('urls', {}).get('listing', {}).get('desktop', '')
                if url.startswith('https://www.ddproperty.com'):
                    full_url = url
                else:
                    full_url = self.base_url + url if url else ''
                
                # // Wyciągnij dane o agencie
                agent = agent_data.get('agent', {})
                
                listings.append({
                    'name': product_data.get('name'),
                    'price': product_data.get('price'),
                    'location': {
                        'district': product_data.get('district'),
                        'region': product_data.get('region'),
                        'area': product_data.get('area'),
                        'district_code': product_data.get('districtCode'),
                        'region_code': product_data.get('regionCode'),
                        'area_code': product_data.get('areaCode')
                    },
                    'property_info': {
                        'bedrooms': product_data.get('bedrooms'),
                        'bathrooms': product_data.get('bathrooms'),
                        'floor_area': product_data.get('floorArea'),
                        'property_type': product_data.get('category'),
                        'furnishing': None  # // Można dodać później z detali ogłoszenia
                    },
                    'listing_info': {
                        'id': product_data.get('id'),
                        'url': full_url,
                        'position': product_data.get('position'),
                        'status': product_data.get('dimension24'),  # // ACT = Active
                        'variant': product_data.get('variant'),  # // Rent/Sale
                    },
                    'agent_info': {
                        'id': agent.get('id'),
                        'name': agent.get('name'),
                        'phone': agent.get('mobile'),
                        'phone_formatted': agent.get('mobilePretty'),
                        'line_id': agent.get('lineId'),
                        'is_verified': bool(agent.get('badges', {}).get('verification')),
                        'verification_date': agent.get('badges', {}).get('verification', {}).get('startDate'),
                        'agency_type': agent_data.get('accountTypeCode'),  # // CORPORATE/NORMAL
                        'profile_image': agent.get('media', {}).get('agent')
                    }
                })
            
            return listings

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response text: {e.response.text[:500]}...")
            return []
