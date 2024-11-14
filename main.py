from dd_property_scraper import DDPropertyScraper
from typing import Dict, Any

def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    // Bezpieczne pobieranie zagnieżdżonych wartości ze słownika
    Args:
        data: Słownik z danymi
        *keys: Klucze do pobrania
        default: Wartość domyślna w przypadku braku danych
    Returns:
        Any: Znaleziona wartość lub wartość domyślna
    """
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError, AttributeError):
        return default

def main():
    # // Inicjalizacja scrapera
    scraper = DDPropertyScraper()
    
    try:
        # // URL z parametrami wyszukiwania
        base_url = f"{scraper.base_url}/en/property-for-rent?region_code=TH83&freetext=Phuket&beds[]=2&listing_type=rent&maxprice=25000&market=residential&search=true"
        
        # // Pobierz dane ze wszystkich stron
        all_listings = scraper.scrape_all_pages(base_url)
        
        # // Wyświetl wyniki
        for i, listing in enumerate(all_listings, 1):
            print(f"\n=== Listing {i} ===")
            print(f"Name: {listing.get('name', 'N/A')}")
            print(f"Price: ฿{listing.get('price', 'N/A')}")
            
            # // Lokalizacja
            location = listing.get('location', {})
            print(f"Location: {location.get('area', 'N/A')}, {location.get('district', 'N/A')}, {location.get('region', 'N/A')}")
            
            # // Informacje o nieruchomości
            property_info = listing.get('property_info', {})
            print(f"Property Type: {property_info.get('property_type', 'N/A')}")
            print(f"Size: {property_info.get('floor_area', 'N/A')}")
            print(f"Bedrooms: {property_info.get('bedrooms', 'N/A')}")
            print(f"Bathrooms: {property_info.get('bathrooms', 'N/A')}")
            print(f"Image URL: {property_info.get('image_url', 'N/A')}")
            
            # // Informacje o ogłoszeniu
            listing_info = listing.get('listing_info', {})
            print(f"Listing ID: {listing_info.get('id', 'N/A')}")
            print(f"Status: {listing_info.get('status', 'N/A')}")
            print(f"URL: {listing_info.get('url', 'N/A')}")
            
            # // Informacje o agencie
            agent_info = listing.get('agent_info', {})
            if agent_info:
                print("\nAgent Information:")
                print(f"Name: {agent_info.get('name', 'N/A')}")
                print(f"Phone: {agent_info.get('phone_formatted', 'N/A')}")
                print(f"Line ID: {agent_info.get('line_id', 'N/A')}")
                print(f"Agency Type: {agent_info.get('agency_type', 'N/A')}")
                print(f"Verified: {'Yes' if agent_info.get('is_verified') else 'No'}")
            
            print("=" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
