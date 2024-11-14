from typing import Tuple, Optional, Dict
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from haversine import haversine
import time
import ssl
import certifi
import geopy.geocoders
import json
import os

class LocationService:
    def __init__(self, cache_file: str = 'location_cache.json'):
        # // Inicjalizacja serwisu lokalizacji
        ctx = ssl.create_default_context(cafile=certifi.where())
        geopy.geocoders.options.default_ssl_context = ctx
        
        self.geolocator = Nominatim(
            user_agent="dd_property_scraper",
            scheme='https',
            timeout=10
        )
        
        # // Współrzędne Patong Beach (predefiniowane dla optymalizacji)
        self.patong_beach_coords = (7.9039, 98.2970)  # (lat, lon)
        
        # // Inicjalizacja cache
        self.cache_file = cache_file
        self.cache = self.load_cache()
        
    def load_cache(self) -> Dict[str, Tuple[float, float]]:
        """
        // Wczytuje cache lokalizacji z pliku
        Returns:
            Dict[str, Tuple[float, float]]: Słownik z zapisanymi współrzędnymi
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    # // Konwertuj listę na tuple podczas wczytywania
                    cache_data = json.load(f)
                    return {k: tuple(v) for k, v in cache_data.items()}
            return {}
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
            return {}
            
    def save_cache(self) -> None:
        """
        // Zapisuje cache lokalizacji do pliku
        """
        try:
            # // Konwertuj tuple na listy do serializacji JSON
            cache_data = {k: list(v) for k, v in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")
    
    def get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        // Pobiera współrzędne dla danej lokalizacji z cache lub z Nominatim
        Args:
            location: String z adresem lokalizacji
        Returns:
            Tuple[float, float]: Para (szerokość, długość) geograficzna lub None
        """
        try:
            # // Sprawdź cache
            if location in self.cache:
                return self.cache[location]
            
            # // Dodaj "Phuket, Thailand" do zapytania dla lepszych wyników
            if "Phuket" not in location:
                location = f"{location}, Phuket, Thailand"
            
            # // Pobierz lokalizację z Nominatim
            time.sleep(1)  # // Przestrzegaj limitów API
            location_data = self.geolocator.geocode(location)
            
            if location_data:
                coords = (location_data.latitude, location_data.longitude)
                self.cache[location] = coords  # // Zapisz w cache
                self.save_cache()  # // Zapisz zaktualizowany cache do pliku
                return coords
            
            return None
            
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            print(f"Error getting coordinates for {location}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error getting coordinates for {location}: {str(e)}")
            return None
    
    def calculate_distance_to_patong(self, location: str) -> Optional[float]:
        """
        // Oblicza odległość między lokalizacją a Patong Beach
        Args:
            location: String z adresem lokalizacji
        Returns:
            float: Odległość w kilometrach lub None w przypadku błędu
        """
        try:
            coords = self.get_coordinates(location)
            if not coords:
                return None
            
            # // Oblicz odległość używając Haversine
            distance = haversine(coords, self.patong_beach_coords)
            return round(distance, 2)  # // Zaokrąglij do 2 miejsc po przecinku
            
        except Exception as e:
            print(f"Error calculating distance for {location}: {str(e)}")
            return None
    
    def get_location_details(self, listing: dict) -> dict:
        """
        // Pobiera szczegóły lokalizacji dla ogłoszenia
        Args:
            listing: Słownik z danymi ogłoszenia
        Returns:
            dict: Słownik z dodatkowymi informacjami o lokalizacji
        """
        try:
            location = listing.get('location', {})
            address_parts = [
                location.get('area'),
                location.get('district'),
                location.get('region')
            ]
            # // Złącz części adresu pomijając None/puste wartości
            address = ", ".join(filter(None, address_parts))
            
            if not address:
                return {
                    'coordinates': None,
                    'distance_to_patong': None,
                    'address': None
                }
            
            coords = self.get_coordinates(address)
            distance = self.calculate_distance_to_patong(address) if coords else None
            
            return {
                'coordinates': coords,
                'distance_to_patong': distance,
                'address': address
            }
            
        except Exception as e:
            print(f"Error getting location details: {str(e)}")
            return {
                'coordinates': None,
                'distance_to_patong': None,
                'address': None
            } 
