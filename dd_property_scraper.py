from curl_cffi import requests
import time
import json
from typing import List, Dict, Any
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

    def safe_get(self, data: Dict, *keys: str, default: Any = None) -> Any:
        """
        // Bezpieczne pobieranie zagnieżdżonych wartości ze słownika
        """
        try:
            for key in keys:
                if not isinstance(data, dict):
                    return default
                data = data.get(key, default)
            return data
        except (AttributeError, TypeError):
            return default

    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        // Pobiera całkowitą liczbę stron z paginacji
        Args:
            soup: BeautifulSoup object strony
        Returns:
            int: Liczba stron
        """
        try:
            pagination = soup.find('div', class_='listing-pagination')
            if not pagination:
                return 1
                
            # // Znajdź wszystkie linki paginacji
            page_links = pagination.find_all('a')
            if not page_links:
                return 1
                
            # // Pobierz numery stron z linków
            pages = [int(link.get('data-page', 1)) for link in page_links if link.get('data-page', '').isdigit()]
            return max(pages) if pages else 1
            
        except Exception as e:
            print(f"Error getting total pages: {str(e)}")
            return 1

    def get_page_url(self, base_url: str, page: int) -> str:
        """
        // Generuje URL dla danej strony
        Args:
            base_url: Podstawowy URL
            page: Numer strony
        Returns:
            str: URL strony
        """
        if page == 1:
            return base_url
        
        # // Dodaj numer strony do URL
        if '/property-for-rent/' in base_url:
            # // URL już zawiera segment /property-for-rent/
            parts = base_url.split('/property-for-rent/')
            return f"{parts[0]}/property-for-rent/{page}?{parts[1].split('?')[1]}"
        else:
            # // Dodaj numer strony przed parametrami
            base_part = base_url.split('?')[0]
            params_part = base_url.split('?')[1]
            return f"{base_part}/{page}?{params_part}"

    def scrape_all_pages(self, base_url: str) -> List[Dict]:
        """
        // Scrapuje wszystkie strony wyników
        Args:
            base_url: Podstawowy URL pierwszej strony
        Returns:
            List[Dict]: Lista wszystkich ogłoszeń
        """
        all_listings = []
        page = 1
        total_pages = None
        
        while True:
            current_url = self.get_page_url(base_url, page)
            print(f"\nScraping page {page}...")
            
            # // Pobierz dane z aktualnej strony
            page_listings, soup = self.extract_listings_data(current_url, return_soup=True)
            
            # // Przy pierwszej stronie sprawdź całkowitą liczbę stron
            if page == 1:
                total_pages = self.get_total_pages(soup)
                print(f"Total pages found: {total_pages}")
            
            if not page_listings:
                print(f"No listings found on page {page}")
                break
                
            all_listings.extend(page_listings)
            print(f"Added {len(page_listings)} listings from page {page}")
            
            if page >= total_pages:
                print("Reached last page")
                break
                
            page += 1
            time.sleep(2)  # // Przerwa między stronami
        
        print(f"\nTotal listings collected: {len(all_listings)}")
        return all_listings

    def extract_listings_data(self, search_url: str, return_soup: bool = False) -> List[Dict]:
        """
        // Pobiera dane o ogłoszeniach z wyników wyszukiwania
        Args:
            search_url (str): URL z parametrami wyszukiwania
            return_soup (bool): Czy zwrócić również obiekt BeautifulSoup
        Returns:
            List[Dict]: Lista ogłoszeń z wymaganymi danymi
            BeautifulSoup: Obiekt soup jeśli return_soup=True
        """
        try:
            # // Najpierw odwiedź stronę główną aby pobrać ciasteczka
            if not hasattr(self, '_visited_home'):
                self.session.get(
                    self.base_url,
                    impersonate=self.impersonate
                )
                self._visited_home = True
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
                return ([], None) if return_soup else []

            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script', {'type': 'text/javascript'})
            target_script = None
            
            for script in script_tags:
                if script.string and 'listingResultsWidget' in script.string:
                    target_script = script
                    break
                    
            if not target_script:
                print("Debug: Could not find script tag with listing data")
                return ([], soup) if return_soup else []

            script_content = target_script.string
            start_idx = script_content.find('var guruApp = ') + len('var guruApp = ')
            end_idx = script_content.find('};', start_idx) + 1
            
            if start_idx == -1 or end_idx == -1:
                print("Debug: Could not find proper JSON data markers")
                return ([], soup) if return_soup else []
                
            json_str = script_content[start_idx:end_idx]
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Debug: JSON parsing error: {str(e)}")
                print(f"Debug: JSON string start: {json_str[:200]}...")
                return ([], soup) if return_soup else []
            
            listings = []
            listings_data = self.safe_get(data, 'listingResultsWidget', 'gaECListings', default=[])
            listings_urls = self.safe_get(data, 'listingResultsWidget', 'listings', default=[])
            
            print(f"Debug: Found {len(listings_data)} listings")
            
            for i, listing in enumerate(listings_data):
                try:
                    product_data = self.safe_get(listing, 'productData', default={})
                    agent_data = listings_urls[i] if i < len(listings_urls) else {}
                    
                    url = self.safe_get(agent_data, 'urls', 'listing', 'desktop', default='')
                    if url.startswith('https://www.ddproperty.com'):
                        full_url = url
                    else:
                        full_url = self.base_url + url if url else ''
                    
                    # // Wyciągnij dane o agencie
                    agent = self.safe_get(agent_data, 'agent', default={})
                    
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
                            'furnishing': None
                        },
                        'listing_info': {
                            'id': product_data.get('id'),
                            'url': full_url,
                            'position': product_data.get('position'),
                            'status': product_data.get('dimension24'),
                            'variant': product_data.get('variant'),
                        },
                        'agent_info': {
                            'id': self.safe_get(agent, 'id'),
                            'name': self.safe_get(agent, 'name'),
                            'phone': self.safe_get(agent, 'mobile'),
                            'phone_formatted': self.safe_get(agent, 'mobilePretty'),
                            'line_id': self.safe_get(agent, 'lineId'),
                            'is_verified': bool(self.safe_get(agent, 'badges', 'verification')),
                            'verification_date': self.safe_get(agent, 'badges', 'verification', 'startDate'),
                            'agency_type': self.safe_get(agent_data, 'accountTypeCode'),
                            'profile_image': self.safe_get(agent, 'media', 'agent')
                        }
                    })
                except Exception as e:
                    print(f"Error processing listing {i}: {str(e)}")
                    continue
            
            return (listings, soup) if return_soup else listings

        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response text: {e.response.text[:500]}...")
            return ([], None) if return_soup else []
