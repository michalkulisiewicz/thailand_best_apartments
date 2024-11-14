from dd_property_scraper import DDPropertyScraper

def main():
    scraper = DDPropertyScraper()
    try:
        result = scraper.make_request("recommendation?type=ldp&locale=en&listingId=10982785&maxItems=8&propertyType=Apartment&listingType=RENT&price=43000&floorArea=83&bedrooms=1")
        print(result)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
