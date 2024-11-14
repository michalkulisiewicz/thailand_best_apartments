from typing import Tuple, Optional, Dict, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from haversine import haversine
import time
import ssl
import certifi
import geopy.geocoders
import json
import os
from models import PropertyListing, Location

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
        
        # // Domyślne punkty referencyjne
        self.reference_points = {
            "Patong Beach": (7.9039, 98.2970)
        }
        
        # // Inicjalizacja cache
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def add_reference_point(self, name: str, location: str) -> Tuple[bool, str]:
        """
        // Dodaje nowy punkt referencyjny
        Args:
            name: Nazwa punktu
            location: Adres lokalizacji
        Returns:
            Tuple[bool, str]: (Sukces/Porażka, Wiadomość)
        """
        try:
            search_query = f"{location}, Phuket, Thailand"
            print(f"Searching for coordinates for: {search_query}")
            
            coords = self.get_coordinates(search_query)
            if coords:
                self.reference_points[name] = coords
                print(f"✅ Successfully added reference point: {name}")
                print(f"📍 Found coordinates: {coords}")
                return True, f"Added {name} at coordinates: {coords}"
            else:
                error_msg = f"❌ Could not find coordinates for: {search_query}"
                print(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error adding reference point: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def remove_reference_point(self, name: str) -> bool:
        """
        // Usuwa punkt referencyjny
        Args:
            name: Nazwa punktu do usunięcia
        Returns:
            bool: True jeśli usunięto pomyślnie
        """
        try:
            if name in self.reference_points and name != "Patong Beach":  # Prevent removing Patong Beach
                del self.reference_points[name]
                return True
            return False
        except Exception as e:
            print(f"Error removing reference point: {str(e)}")
            return False
    
    def calculate_distances(self, coords: Tuple[float, float]) -> Dict[str, float]:
        """
        // Oblicza odległość do wszystkich punktów referencyjnych
        Args:
            coords: Współrzędne lokalizacji
        Returns:
            Dict[str, float]: Słownik z odległościami do punktów referencyjnych
        """
        distances = {}
        for name, ref_coords in self.reference_points.items():
            try:
                distance = haversine(coords, ref_coords)
                distances[name] = round(distance, 2)
            except Exception as e:
                print(f"Error calculating distance to {name}: {str(e)}")
                distances[name] = None
        return distances

    def get_location_details(self, listing: PropertyListing) -> Location:
        """
        // Pobiera szczegóły lokalizacji dla ogłoszenia
        Args:
            listing: Obiekt PropertyListing
        Returns:
            Location: Zaktualizowany obiekt Location
        """
        try:
            location = listing.location
            address_parts = [
                location.area,
                location.district,
                location.region
            ]
            # // Złącz części adresu pomijając None/puste wartości
            address = ", ".join(filter(None, address_parts))
            
            if not address:
                return location
            
            coords = self.get_coordinates(address)
            if coords:
                location.coordinates = coords
                # // Oblicz odległości do wszystkich punktów referencyjnych
                location.distances = self.calculate_distances(coords)
                print(f"Calculated distances for {address}: {location.distances}")  # Debug print
            
            location.address = address
            return location
            
        except Exception as e:
            print(f"Error getting location details: {str(e)}")
            return listing.location
    
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
            
            # // Wyciągnij samą nazwę obszaru i dodaj ", Thailand"
            location_parts = location.split(',')
            area = location_parts[0].strip()
            search_query = f"{area}, Thailand"
            
            # // Pobierz lokalizację z Nominatim
            time.sleep(1)  # // Przestrzegaj limitów API
            location_data = self.geolocator.geocode(search_query)
            
            if location_data:
                coords = (location_data.latitude, location_data.longitude)
                # // Zapisz w cache oryginalną lokalizację
                self.cache[location] = coords
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
 