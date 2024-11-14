from curl_cffi import requests
import time
import json

class DDPropertyScraper:
    def __init__(self):
        # // Inicjalizacja podstawowych ustawień
        self.base_url = "https://www.ddproperty.com/api/consumer/"
        self.headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.ddproperty.com/',
            'Origin': 'https://www.ddproperty.com',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        # // Inicjalizacja sesji
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.impersonate = "chrome110" # // Udawaj Chrome 110

    def make_request(self, endpoint: str) -> dict:
        """
        // Wykonuje żądanie GET do określonego endpointu
        Args:
            endpoint (str): Ścieżka URL do odpytania
        Returns:
            dict: Odpowiedź z serwera w formacie JSON
        """
        try:
            # // Najpierw odwiedź stronę główną aby pobrać ciasteczka
            self.session.get(
                'https://www.ddproperty.com/',
                impersonate=self.impersonate
            )
            time.sleep(2)  # // Krótka przerwa
            
            url = f"{self.base_url}{endpoint}"
            print(f"Making request to: {url}")
            
            response = self.session.get(
                url,
                impersonate=self.impersonate,
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Response text: {response.text}")
                response.raise_for_status()
                
        except Exception as e:
            print(f"Error during request: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text}")
            raise
