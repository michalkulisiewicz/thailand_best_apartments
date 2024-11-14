from location_service import LocationService
from models import PropertyListing, Location
from typing import List

def test_locations():
    # // Inicjalizacja serwisu
    location_service = LocationService()
    
    # // Lista testowych lokalizacji
    test_cases = [
        PropertyListing(
            name="Test Property 1",
            location=Location(
                area="Rawai",
                district="Muang Phuket",
                region="Phuket"
            )
        ),
        PropertyListing(
            name="Test Property 2",
            location=Location(
                area="Patong",
                district="Kathu",
                region="Phuket"
            )
        ),
        PropertyListing(
            name="Test Property 3",
            location=Location(
                area="Mai Khao",
                district="Thalang",
                region="Phuket"
            )
        ),
        PropertyListing(
            name="Test Property 4",
            location=Location(
                area="Chalong",
                district="Muang Phuket",
                region="Phuket"
            )
        )
    ]
    
    # // Testuj każdą lokalizację
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Testing Location {i} ===")
        print(f"Property: {test_case.name}")
        print("Original location data:")
        print(f"Area: {test_case.location.area}")
        print(f"District: {test_case.location.district}")
        print(f"Region: {test_case.location.region}")
        
        # // Pobierz zaktualizowane dane o lokalizacji
        updated_location = location_service.get_location_details(test_case)
        
        print("\nUpdated location data:")
        print(f"Area: {updated_location.area}")
        print(f"District: {updated_location.district}")
        print(f"Region: {updated_location.region}")
        print(f"Coordinates: {updated_location.coordinates}")
        print(f"Distance to Patong: {updated_location.distance_to_patong:.2f} km" if updated_location.distance_to_patong else "Distance to Patong: N/A")
        print(f"Full address: {updated_location.address}")
        print("=" * 50)

def test_single_location(area: str, district: str = "Muang Phuket", region: str = "Phuket"):
    """
    // Testuje pojedynczą lokalizację
    Args:
        area: Nazwa obszaru
        district: Nazwa dystryktu (domyślnie Muang Phuket)
        region: Nazwa regionu (domyślnie Phuket)
    """
    location_service = LocationService()
    
    test_case = PropertyListing(
        name=f"Test Property - {area}",
        location=Location(
            area=area,
            district=district,
            region=region
        )
    )
    
    print(f"\n=== Testing Single Location ===")
    print(f"Property: {test_case.name}")
    print("Original location data:")
    print(f"Area: {test_case.location.area}")
    print(f"District: {test_case.location.district}")
    print(f"Region: {test_case.location.region}")
    
    updated_location = location_service.get_location_details(test_case)
    
    print("\nUpdated location data:")
    print(f"Area: {updated_location.area}")
    print(f"District: {updated_location.district}")
    print(f"Region: {updated_location.region}")
    print(f"Coordinates: {updated_location.coordinates}")
    print(f"Distance to Patong: {updated_location.distance_to_patong:.2f} km" if updated_location.distance_to_patong else "Distance to Patong: N/A")
    print(f"Full address: {updated_location.address}")
    print("=" * 50)

if __name__ == "__main__":
    # // Test wszystkich lokalizacji
    test_locations()
    
    # // Test pojedynczej lokalizacji
    # test_single_location("Rawai")
    # test_single_location("Patong", "Kathu")
    # test_single_location("Kamala", "Kathu") 
