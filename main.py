from dd_property_scraper import DDPropertyScraper
from location_service import LocationService
from models import PropertyListing

def main():
    # // Inicjalizacja serwisów
    scraper = DDPropertyScraper()
    location_service = LocationService()
    
    try:
        # // URL z parametrami wyszukiwania
        base_url = f"{scraper.base_url}/en/property-for-rent?region_code=TH83&freetext=Phuket&beds[]=2&listing_type=rent&maxprice=25000&market=residential&search=true"
        
        # // Pobierz dane ze wszystkich stron
        all_listings = scraper.scrape_all_pages(base_url)
        
        # // Wyświetl wyniki
        for i, listing in enumerate(all_listings, 1):
            # // Pobierz informacje o lokalizacji
            location_details = location_service.get_location_details(listing)
            
            print(f"\n=== Listing {i} ===")
            print(f"Name: {listing.name or 'N/A'}")
            print(f"Price: ฿{listing.price or 'N/A'}")
            
            # // Lokalizacja
            location = listing.location
            print(f"Location: {location.area or 'N/A'}, {location.district or 'N/A'}, {location.region or 'N/A'}")
            if location.coordinates:
                print(f"Coordinates: {location.coordinates}")
            if location.distance_to_patong is not None:
                print(f"Distance to Patong Beach: {location.distance_to_patong} km")
            
            # // Informacje o nieruchomości
            property_info = listing.property_info
            print(f"Property Type: {property_info.property_type or 'N/A'}")
            print(f"Size: {property_info.floor_area or 'N/A'}")
            print(f"Bedrooms: {property_info.bedrooms or 'N/A'}")
            print(f"Bathrooms: {property_info.bathrooms or 'N/A'}")
            print(f"Image URL: {property_info.image_url or 'N/A'}")
            
            # // Informacje o ogłoszeniu
            listing_info = listing.listing_info
            print(f"Listing ID: {listing_info.id or 'N/A'}")
            print(f"Status: {listing_info.status or 'N/A'}")
            print(f"URL: {listing_info.url or 'N/A'}")
            
            # // Informacje o agencie
            agent_info = listing.agent_info
            if agent_info:
                print("\nAgent Information:")
                print(f"Name: {agent_info.name or 'N/A'}")
                print(f"Phone: {agent_info.phone_formatted or 'N/A'}")
                print(f"Line ID: {agent_info.line_id or 'N/A'}")
                print(f"Agency Type: {agent_info.agency_type or 'N/A'}")
                print(f"Verified: {'Yes' if agent_info.is_verified else 'No'}")
            
            print("=" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
