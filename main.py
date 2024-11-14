from dd_property_scraper import DDPropertyScraper

def main():
    # // Inicjalizacja scrapera
    scraper = DDPropertyScraper()
    
    try:
        # // URL z parametrami wyszukiwania
        search_url = f"{scraper.base_url}/en/property-for-rent?region_code=TH83&freetext=Phuket&beds[]=2&listing_type=rent&maxprice=25000&market=residential&search=true"
        
        # // Pobierz dane o ogłoszeniach
        listings = scraper.extract_listings_data(search_url)
        
        # // Wyświetl wyniki
        for listing in listings:
            print("\n--- Listing ---")
            print(f"Name: {listing['name']}")
            print(f"Price: ฿{listing['price']}")
            print(f"Location: {listing['location']['area']}, {listing['location']['district']}, {listing['location']['region']}")
            print(f"Size: {listing['floor_area']}")
            print(f"Bedrooms: {listing['bedrooms']}")
            print(f"Bathrooms: {listing['bathrooms']}")
            print(f"URL: {listing['url']}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
