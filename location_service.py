from typing import Tuple, Optional, Dict, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from haversine import haversine
import time
import ssl
import certifi
import geopy.geocoders
from models import PropertyListing, Location

class LocationService:
    DEFAULT_REFERENCE_POINTS = {
        "Phuket": {
            "Patong Beach": (7.9039, 98.2970)
        },
        "Bangkok": {
            "Siam": (13.7466, 100.5339)
        },
        "Chiang Mai": {
            "Old City": (18.7883, 98.9853)
        },
        "Chiang Rai": {
            "City Center": (19.9071, 99.8305)
        }
    }
    
    def __init__(self):
        # // Inicjalizacja serwisu lokalizacji
        ctx = ssl.create_default_context(cafile=certifi.where())
        geopy.geocoders.options.default_ssl_context = ctx
        
        self.geolocator = Nominatim(
            user_agent="dd_property_scraper",
            scheme='https',
            timeout=10
        )
        
        # // Inicjalizacja cache w pamięci
        self.location_cache = {}
        
        # // Inicjalizacja punktów referencyjnych
        self.reference_points = {}
        self.current_city = "Phuket"  # Default city
        self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """
        // Resetuje punkty referencyjne do wartości domyślnych dla aktualnego miasta
        """
        self.reference_points = self.DEFAULT_REFERENCE_POINTS[self.current_city].copy()
    
    def set_city(self, city: str):
        """
        // Zmienia aktywne miasto i resetuje punkty referencyjne
        """
        if city in self.DEFAULT_REFERENCE_POINTS:
            self.current_city = city
            self.reset_to_defaults()
    
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
            # // Sprawdź czy nazwa nie jest już używana
            if name in self.reference_points:
                return False, f"Reference point '{name}' already exists"
                
            search_query = f"{location}, {self.current_city}, Thailand"
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
            if name in self.reference_points:
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
    
    def get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        // Pobiera współrzędne dla danej lokalizacji z cache lub z Nominatim
        Args:
            location: String z adresem lokalizacji
        Returns:
            Tuple[float, float]: Para (szerokość, długość) geograficzna lub None
        """
        try:
            # // Sprawdź cache w pamięci
            if location in self.location_cache:
                return self.location_cache[location]
            
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
                self.location_cache[location] = coords
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
 