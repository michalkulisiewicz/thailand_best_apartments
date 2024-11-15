import streamlit as st
from dd_property_scraper import DDPropertyScraper
from location_service import LocationService
import folium
from streamlit_folium import st_folium
from typing import List
from models import PropertyListing
from currency_service import CurrencyService

def build_search_url(params: dict) -> str:
    """
    // Buduje URL wyszukiwania na podstawie parametrów
    Args:
        params: Słownik z parametrami wyszukiwania
    Returns:
        str: Pełny URL wyszukiwania
    """
    base_url = "https://www.ddproperty.com/en/property-for-rent"
    query_parts = []
    
    # // Add city and corresponding region code
    city_region_codes = {
        "Phuket": "TH83",
        "Bangkok": "TH10",
        "Chiang Mai": "TH50",
        "Chiang Rai": "TH57"
    }
    
    # // Get the current city from session state
    current_city = st.session_state.get('current_city', 'Phuket')
    region_code = city_region_codes.get(current_city, 'TH83')  # Default to Phuket if not found
    
    # // Add city-specific parameters
    query_parts.append(("freetext", current_city))
    query_parts.append(("region_code", region_code))
    query_parts.append(("market", "residential"))
    query_parts.append(("search", "true"))
    
    # // Add remaining parameters if they are set
    if params.get("min_price"):
        query_parts.append(("minprice", params["min_price"]))
        
    if params.get("max_price"):
        query_parts.append(("maxprice", params["max_price"]))
        
    if params.get("bedrooms"):
        for bed in params["bedrooms"]:
            query_parts.append(("beds[]", bed))
            
    if params.get("bathrooms"):
        for bath in params["bathrooms"]:
            query_parts.append(("baths[]", bath))
            
    if params.get("property_types"):
        for p_type in params["property_types"]:
            query_parts.append(("property_type_code[]", p_type))
            
    if params.get("furnishing"):
        for furn in params["furnishing"]:
            query_parts.append(("furnishing[]", furn))
            
    if params.get("max_size"):
        query_parts.append(("maxsize", params["max_size"]))
    
    # // Join all parameters into URL
    query_string = "&".join(f"{k}={v}" for k, v in query_parts)
    return f"{base_url}?{query_string}"

def scrape_listings(max_pages: int = None, search_params: dict = None) -> List[PropertyListing]:
    """
    // Pobiera ogłoszenia z DD Property i oblicza odległości
    """
    scraper = DDPropertyScraper()
    location_service = st.session_state['location_service']
    
    # // Użyj parametrów wyszukiwania do zbudowania URL
    base_url = build_search_url(search_params or {})
    listings = scraper.scrape_all_pages(base_url, max_pages=max_pages)
    
    # // Dodaj informacje o lokalizacji i odległościach
    for listing in listings:
        # // Upewnij się, że mamy wszystkie odległości
        location_service.get_location_details(listing)
        
        # // Debug print
        print(f"\nListing: {listing.name}")
        print("Distances:", listing.location.distances)
    
    return listings

def create_map(listings: List[PropertyListing]):
    """
    // Tworzy mapę z zaznaczonymi lokalizacjami
    """
    # // Define city center coordinates
    city_centers = {
        "Phuket": [7.9519, 98.3381],
        "Bangkok": [13.7563, 100.5018],
        "Chiang Mai": [18.7883, 98.9853],
        "Chiang Rai": [19.9071, 99.8305]
    }
    
    # // Get current city from session state and set map center
    current_city = st.session_state.get('current_city', 'Phuket')
    center_coords = city_centers.get(current_city, [7.9519, 98.3381])  # Default to Phuket if city not found
    
    # // Set appropriate zoom level for each city
    zoom_levels = {
        "Phuket": 11,
        "Bangkok": 12,
        "Chiang Mai": 12,
        "Chiang Rai": 13
    }
    zoom_start = zoom_levels.get(current_city, 11)
    
    # // Create map centered on selected city
    m = folium.Map(location=center_coords, zoom_start=zoom_start)
    
    # // Add all reference points
    for name, coords in st.session_state['location_service'].reference_points.items():
        folium.Marker(
            coords,
            popup=name,
            tooltip=name,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # // Group listings by coordinates
    location_groups = {}
    for listing in listings:
        if listing.location.coordinates:
            coords = listing.location.coordinates
            coords_key = f"{coords[0]:.6f},{coords[1]:.6f}"
            
            if coords_key not in location_groups:
                location_groups[coords_key] = {
                    'coordinates': coords,
                    'listings': [],
                    'area': listing.location.area
                }
            location_groups[coords_key]['listings'].append(listing)
    
    # // Add markers for each location
    for location_data in location_groups.values():
        listings = location_data['listings']
        coords = location_data['coordinates']
        area = location_data['area']
        
        # // Create HTML for popup with multiple listings
        popup_html = f"""
            <div style="max-width:300px; overflow-y:auto;">
                <style>
                    .popup-container {{ padding: 5px; }}
                    .property-card {{
                        margin-bottom: 15px;
                        padding: 10px;
                        border: 1px solid #eee;
                        border-radius: 5px;
                        background-color: white;
                    }}
                    .property-title {{
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .property-price {{
                        color: #FF4B4B;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .property-details {{
                        font-size: 0.9em;
                        margin-bottom: 5px;
                    }}
                    .view-button {{
                        background-color: #FF4B4B;
                        color: white;
                        padding: 5px 10px;
                        text-decoration: none;
                        border-radius: 3px;
                        display: inline-block;
                        margin-top: 5px;
                    }}
                    .view-button:hover {{
                        background-color: #FF3333;
                    }}
                    .location-header {{
                        background-color: #f8f9fa;
                        padding: 10px;
                        margin-bottom: 10px;
                        border-radius: 5px;
                        text-align: center;
                    }}
                    .distances-list {{
                        margin: 5px 0;
                        font-size: 0.9em;
                    }}
                    .listing-separator {{
                        height: 1px;
                        background: linear-gradient(
                            to right,
                            rgba(255, 75, 75, 0),
                            rgba(255, 75, 75, 1) 10%,
                            rgba(255, 75, 75, 1) 90%,
                            rgba(255, 75, 75, 0)
                        );
                        margin: 1rem 0;
                        border: none;
                        opacity: 0.8;
                    }}
                </style>
                <div class="popup-container">
                    <div class="location-header">
                        <h4>{area} - {len(listings)} properties</h4>
                    </div>
        """
        
        for i, listing in enumerate(listings):
            distances_html = "<div class='distances-list'>"
            for loc_name, distance in listing.location.distances.items():
                distances_html += f"🎯 {distance:.1f} km to {loc_name}<br>"
            distances_html += "</div>"
            
            popup_html += f"""
                <div class="property-card">
                    <div class="property-title">{listing.name}</div>
                    <div class="property-price">฿{listing.price:,}/month</div>
                    <div class="property-details">
                        {listing.property_info.bedrooms} bed, {listing.property_info.bathrooms} bath<br>
                        Size: {listing.property_info.floor_area}
                    </div>
                    {distances_html}
                    <a href="{listing.listing_info.url}" target="_blank" class="view-button">
                        View Property
                    </a>
                </div>
            """
            # Add separator between cards, but not after the last one
            if i < len(listings) - 1:
                popup_html += '<div class="listing-separator"></div>'
        
        popup_html += "</div></div>"
        
        # // Create marker with icon showing number of listings
        icon = folium.DivIcon(
            html=f"""
                <div style="background-color:#FF4B4B; color:white; 
                          border-radius:50%; width:25px; height:25px; 
                          display:flex; align-items:center; justify-content:center; 
                          font-weight:bold; font-size:12px;">
                    {len(listings)}
                </div>
            """
        )
        
        # // Add marker to map with larger popup
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=300, max_height=500),
            tooltip=f"{area} - {len(listings)} properties",
            icon=icon
        ).add_to(m)
    
    return m

def sort_listings(listings: List[PropertyListing], sort_by: str) -> List[PropertyListing]:
    """
    // Sortuje listę ogłoszeń według wybranego kryterium
    Args:
        listings: Lista ogłoszeń
        sort_by: Kryterium sortowania
    Returns:
        List[PropertyListing]: Posortowana lista ogłoszeń
    """
    if sort_by == "price_low_high":
        return sorted(listings, key=lambda x: x.price or float('inf'))
    elif sort_by == "price_high_low":
        return sorted(listings, key=lambda x: x.price or float('-inf'), reverse=True)
    return listings

def main():
    st.set_page_config(
        page_title="DD Property Listings",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # // Initialize LocationService in session state if not exists
    if 'location_service' not in st.session_state:
        st.session_state['location_service'] = LocationService()
    
    # // Initialize CurrencyService in session state
    if 'currency_service' not in st.session_state:
        st.session_state['currency_service'] = CurrencyService()
    
    # // Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 1rem;
        }
        .stButton>button {
            width: 100%;
        }
        .listing-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: white;
        }
        .price-tag {
            font-size: 1.5rem;
            color: #FF4B4B;
            font-weight: bold;
        }
        .property-stats {
            display: flex;
            justify-content: space-between;
            margin: 1rem 0;
        }
        .listing-separator {
            height: 1px;
            background: linear-gradient(
                to right,
                rgba(255, 75, 75, 0),
                rgba(255, 75, 75, 1) 10%,
                rgba(255, 75, 75, 1) 90%,
                rgba(255, 75, 75, 0)
            );
            margin: 1rem 0;
            border: none;
            opacity: 0.8;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # // Add custom CSS for sidebar styling
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #1A1C1E;
            padding: 1rem;
        }
        .st-emotion-cache-1cypcdb {
            background-color: #1A1C1E;
        }
        [data-testid="stSidebarNav"] {
            background-color: #1A1C1E;
        }
        .st-emotion-cache-16txtl3 {
            padding: 1rem;
        }
        .sidebar-header {
            color: #FF4B4B;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .sidebar-section {
            background-color: transparent;
            padding: 0.5rem 0;
            margin-bottom: 0;
        }
        .section-separator {
            height: 1px;
            background: linear-gradient(
                to right,
                rgba(255, 75, 75, 0),
                rgba(255, 75, 75, 1) 10%,
                rgba(255, 75, 75, 1) 90%,
                rgba(255, 75, 75, 0)
            );
            margin: 0.5rem 0;
            border: none;
            opacity: 0.8;
        }
        /* Style for select boxes */
        .stSelectbox > div > div {
            background-color: #2A2D2F;
            border: 1px solid #3A3D3F;
        }
        /* Style for number inputs */
        .stNumberInput > div > div > input {
            background-color: #2A2D2F;
            border: 1px solid #3A3D3F;
        }
        /* Style for radio buttons */
        .stRadio > div {
            background-color: #2A2D2F;
            padding: 1rem;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Filip's Property Finder 🌴")
    
    # // Sidebar controls
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🌴 Search Settings</div>', unsafe_allow_html=True)
        
        # // City Selection
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        selected_city = st.selectbox(
            "Select City",
            options=["Phuket", "Bangkok", "Chiang Mai", "Chiang Rai"],
            index=0,
            key="city_selector"
        )
        
        # // Update location service if city changes
        if 'current_city' not in st.session_state or st.session_state.current_city != selected_city:
            st.session_state.current_city = selected_city
            st.session_state['location_service'].set_city(selected_city)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Scraping Mode
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📊 Scraping Mode")
        scrape_mode = st.radio(
            "Choose scraping mode",
            options=["Specific pages", "All pages"],
            help="Choose whether to scrape a specific number of pages or all available pages"
        )
        
        if scrape_mode == "Specific pages":
            max_pages = st.number_input("Number of pages to scrape", min_value=1, value=1)
        else:
            max_pages = None
            st.info("Will scrape all available pages")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Property Filters
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("🏠 Property Filters")
        
        # // Currency selection for price input
        price_currency = st.radio(
            "Price Currency",
            options=["THB", "PLN"],
            horizontal=True
        )
        
        # // Price range with currency conversion
        col1, col2 = st.columns(2)
        with col1:
            if price_currency == "THB":
                min_price = st.number_input(
                    "Minimum Price (THB/month)", 
                    min_value=0,
                    max_value=1000000,
                    value=0,
                    step=1000
                )
            else:
                min_price_pln = st.number_input(
                    "Minimum Price (PLN/month)", 
                    min_value=0,
                    max_value=1000000,
                    value=0,
                    step=100
                )
                # Convert PLN to THB
                min_price = int(min_price_pln / float(st.session_state['currency_service'].thb_to_pln_rate)) if min_price_pln > 0 else 0
        
        with col2:
            if price_currency == "THB":
                max_price = st.number_input(
                    "Maximum Price (THB/month)", 
                    min_value=0,
                    max_value=1000000,
                    value=25000,
                    step=1000
                )
            else:
                max_price_pln = st.number_input(
                    "Maximum Price (PLN/month)", 
                    min_value=0,
                    max_value=1000000,
                    value=int(25000 * float(st.session_state['currency_service'].thb_to_pln_rate)),
                    step=100
                )
                # Convert PLN to THB
                max_price = int(max_price_pln / float(st.session_state['currency_service'].thb_to_pln_rate)) if max_price_pln > 0 else 0
        
        # // Show conversion info
        if price_currency == "PLN":
            st.info(f"""
                Converted to THB:
                Min: {min_price:,} THB/month
                Max: {max_price:,} THB/month
            """)
        
        # // Add validation for min/max price
        if min_price > max_price and max_price != 0:
            st.error("Minimum price cannot be greater than maximum price")
            min_price = 0
        
        # // Property type selection
        property_type = st.selectbox(
            "Property Type",
            options=[
                "Any",
                "Condominium",
                "Detached House",
                "Villa",
                "Townhouse",
                "Land",
                "Apartment"
            ],
            index=0
        )
        
        # // Convert display name to code for property type
        property_type_mapping = {
            "Condominium": "CONDO",
            "Detached House": "BUNG",
            "Villa": "VIL",
            "Townhouse": "TOWN",
            "Land": "LAND",
            "Apartment": "APT"
        }
        
        # // Bedrooms
        bedrooms = st.selectbox(
            "Number of Bedrooms",
            options=['Any', '1', '2', '3', '4', '5', '5+'],
            index=0
        )
        
        # // Bathrooms
        bathrooms = st.selectbox(
            "Number of Bathrooms",
            options=['Any', '1', '2', '3', '4', '5', '5+'],
            index=0
        )
        
        # // Furnishing
        furnishing_type = st.selectbox(
            "Furnishing",
            options=[
                "Any",
                "Fully Furnished",
                "Partially Furnished",
                "Unfurnished"
            ],
            index=0
        )
        
        # // Convert display name to code for furnishing
        furnishing_mapping = {
            "Fully Furnished": "FULL",
            "Partially Furnished": "PART",
            "Unfurnished": "UNFUR"
        }
        
        # // Maximum size
        max_size = st.number_input(
            "Maximum Size (sqm)", 
            min_value=0,
            value=0,
            help="Leave as 0 for no size limit"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Sort Properties
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📊 Sort Properties")
        sort_option = st.selectbox(
            "Sort by price",
            options=[
                "default",
                "price_low_high",
                "price_high_low"
            ],
            format_func=lambda x: {
                "default": "Default",
                "price_low_high": "Price: Low to High",
                "price_high_low": "Price: High to Low"
            }[x]
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Reference Locations
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📍 Reference Locations")
        
        # // Add new reference point
        with st.expander("Add New Reference Location", expanded=False):
            new_location_name = st.text_input("Location Name")
            new_location_address = st.text_input("Location Address")
            if st.button("Add Location"):
                if new_location_name and new_location_address:
                    success, message = st.session_state['location_service'].add_reference_point(
                        new_location_name, 
                        new_location_address
                    )
                    if success:
                        st.success(message)
                        if 'listings' in st.session_state:
                            with st.spinner('Updating distances...'):
                                for listing in st.session_state['listings']:
                                    st.session_state['location_service'].get_location_details(listing)
                                st.session_state['map'] = create_map(st.session_state['listings'])
                            st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both name and address")
        
        # // Display current reference points
        st.write("Current Reference Points:")
        
        # // Display points with delete buttons
        for name, coords in st.session_state['location_service'].reference_points.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📍 {name} ({coords[0]:.4f}, {coords[1]:.4f})")
            with col2:
                if st.button("🗑️", key=f"remove_{name}"):
                    if st.session_state['location_service'].remove_reference_point(name):
                        if not st.session_state['location_service'].reference_points:
                            st.session_state['location_service'].reset_to_defaults()
                        if 'listings' in st.session_state:
                            with st.spinner('Updating distances...'):
                                for listing in st.session_state['listings']:
                                    st.session_state['location_service'].get_location_details(listing)
                                st.session_state['map'] = create_map(st.session_state['listings'])
                        st.rerun()
        
        # // Reset button moved here, after displaying current points
        if st.button("Reset to Default Points"):
            st.session_state['location_service'].reset_to_defaults()
            if 'listings' in st.session_state:
                with st.spinner('Updating distances...'):
                    for listing in st.session_state['listings']:
                        st.session_state['location_service'].get_location_details(listing)
                    st.session_state['map'] = create_map(st.session_state['listings'])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Currency Exchange
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("💱 Currency Exchange")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"1 THB = {st.session_state['currency_service'].thb_to_pln_rate:.4f} PLN")
            last_update = st.session_state['currency_service'].get_last_update_time()
            if last_update:
                st.write(f"Last updated: {last_update}")
        with col2:
            refresh = st.button("🔄", help="Refresh exchange rate")
        
        # // Show success/error message under the rate
        if refresh:
            rate, error = st.session_state['currency_service'].get_current_rate()
            if error:
                st.error(error)
            else:
                st.success(f"Updated: 1 THB = {rate:.4f} PLN")
                if 'listings' in st.session_state:
                    for listing in st.session_state['listings']:
                        listing.price_pln = st.session_state['currency_service'].convert_to_pln(listing.price)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
        
        # // Search button at the bottom
        # // Prepare search parameters with THB values
        search_params = {
            "min_price": min_price if min_price > 0 else None,
            "max_price": max_price if max_price > 0 else None,
            "property_types": [property_type_mapping[property_type]] if property_type != "Any" else None,
            "bedrooms": bedrooms if bedrooms != 'Any' else None,
            "bathrooms": bathrooms if bathrooms != 'Any' else None,
            "furnishing": [furnishing_mapping[furnishing_type]] if furnishing_type != "Any" else None,
            "max_size": max_size if max_size > 0 else None
        }
        
        # // Clean up None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        if st.button("🔍 Search Properties", use_container_width=True):
            with st.spinner('Fetching properties...'):
                listings = scrape_listings(max_pages, search_params)
                if listings:
                    st.session_state['listings'] = listings
                    st.session_state['map'] = create_map(listings)
                    st.success(f'Found {len(listings)} properties!')
                else:
                    st.error("No properties found. Please try again.")
    
    # // Main content
    if 'listings' not in st.session_state:
        st.info("👈 Set your search parameters and click 'Search Properties' to start")
        return
    
    # // Sort listings if needed
    sorted_listings = sort_listings(st.session_state['listings'], sort_option)
    
    # // Display map
    st.subheader("📍 Property Locations")
    st_folium(st.session_state['map'], use_container_width=True, height=600)
    
    # // Display listings in grid
    st.subheader("🏠 Available Properties")
    
    # // Update the CSS for listing cards in the main content area
    st.markdown("""
        <style>
            .listing-card {
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                height: 700px;
                border: none;
                display: flex;
                flex-direction: column;
            }
            .property-image {
                width: 100%;
                height: 250px;
                object-fit: cover;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            .property-title {
                font-weight: bold;
                color: white;
                height: 48px;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                margin-bottom: 10px;
                font-size: 16px;
            }
            .price-container {
                height: 60px;
                margin-bottom: 10px;
            }
            .price-tag {
                font-size: 20px;
                color: #FF4B4B;
                font-weight: bold;
                margin: 5px 0;
            }
            .price-pln {
                font-size: 16px;
                color: #FF4B4B;
                opacity: 0.8;
            }
            .property-details {
                margin: 10px 0;
                color: #CCCCCC;
                flex-grow: 1;
                overflow-y: auto;
                line-height: 1.6;
            }
            .view-button {
                background-color: #FF4B4B;
                color: white;
                padding: 10px;
                text-align: center;
                border-radius: 5px;
                text-decoration: none;
                display: block;
                margin-top: auto;
            }
            .view-button:hover {
                background-color: #FF3333;
            }
            .listing-separator {
                height: 1px;
                background: linear-gradient(
                    to right,
                    rgba(255, 75, 75, 0),
                    rgba(255, 75, 75, 1) 10%,
                    rgba(255, 75, 75, 1) 90%,
                    rgba(255, 75, 75, 0)
                );
                margin: 1.5rem 0;
                border: none;
                opacity: 0.8;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # // In the grid layout section, update how we display listings:
    cols = st.columns(3)
    
    for i, listing in enumerate(sorted_listings):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                    <div class="listing-card">
                        <img src="{listing.property_info.image_url or 'https://via.placeholder.com/400x300?text=No+Image'}" class="property-image">
                        <div class="property-title">{listing.name}</div>
                        <div class="price-container">
                            <div class="price-tag">฿{listing.price:,}/month</div>
                            <div class="price-pln">(~{listing.price_pln:,.2f} PLN/month)</div>
                        </div>
                        <div class="property-details">
                            🛏️ {listing.property_info.bedrooms} beds<br>
                            🚿 {listing.property_info.bathrooms} baths<br>
                            📏 {listing.property_info.floor_area}<br>
                            🏠 {listing.property_info.property_type}<br>
                            📍 {listing.location.area}, {listing.location.district}<br>
                            <br>
                            {' '.join(f'🎯 {distance:.1f} km to {loc_name}<br>' for loc_name, distance in listing.location.distances.items())}
                        </div>
                        <a href="{listing.listing_info.url}" target="_blank" class="view-button">View Property</a>
                    </div>
                    {'<div class="listing-separator"></div>' if i < len(sorted_listings) - 1 else ''}
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
