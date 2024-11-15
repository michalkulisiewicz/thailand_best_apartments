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
    
    # // Zawsze dodaj miasto i residential market
    query_parts.append(("freetext", params.get("city", "Phuket")))
    query_parts.append(("region_code", params.get("region_code", "TH83")))  # Default to Phuket
    query_parts.append(("market", "residential"))
    query_parts.append(("search", "true"))
    
    # // Dodaj pozostałe parametry jeśli są ustawione
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
    
    # // Złącz wszystkie parametry w URL
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
    # // Centrum Phuket
    m = folium.Map(location=[7.9519, 98.3381], zoom_start=11)
    
    # // Dodaj wszystkie punkty referencyjne
    for name, coords in st.session_state['location_service'].reference_points.items():
        folium.Marker(
            coords,
            popup=name,
            tooltip=name,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # // Grupuj oferty po współrzędnych
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
    
    # // Dodaj markery dla każdej lokalizacji
    for location_data in location_groups.values():
        listings = location_data['listings']
        coords = location_data['coordinates']
        area = location_data['area']
        
        # // Tworzenie HTML dla popup z wieloma ofertami
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
                </style>
                <div class="popup-container">
                    <div class="location-header">
                        <h4>{area} - {len(listings)} properties</h4>
                    </div>
        """
        
        for listing in listings:
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
        
        popup_html += "</div></div>"
        
        # // Twórz marker z ikoną pokazującą liczbę ofert (zawsze używaj czerwonego kółka z numerem)
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
        
        # // Dodaj marker do mapy z większym popupem
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
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # // Initialize services in session state if not exists
    if 'location_service' not in st.session_state:
        st.session_state['location_service'] = LocationService()
    if 'currency_service' not in st.session_state:
        st.session_state['currency_service'] = CurrencyService()
    
    # // Define city options with their region codes
    CITIES = {
        "Phuket": "TH83",
        "Bangkok": "TH10",
        "Chiang Mai": "TH50",
        "Chiang Rai": "TH57"
    }
    
    # // Sidebar controls
    with st.sidebar:
        # // Add custom CSS for better sidebar styling
        st.markdown("""
            <style>
                .sidebar-header {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #FF4B4B;
                }
                .sidebar-subheader {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #FF4B4B;
                }
                .sidebar-section {
                    padding: 0px;  /* Removed padding */
                    margin-bottom: 10px;
                }
                .reference-point {
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 8px;
                }
                .currency-info {
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
                .search-button {
                    background-color: #FF4B4B;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    text-align: center;
                    margin-top: 20px;
                }
                /* Add spacing between section title and content */
                .stRadio, .stSelectbox {
                    margin-top: 5px;
                }
            </style>
        """, unsafe_allow_html=True)

        # // Main header
        st.markdown('<p class="sidebar-header">Search Settings</p>', unsafe_allow_html=True)
        
        # // City Selection Section
        selected_city = st.selectbox(
            "🌆 Select City",
            options=list(CITIES.keys()),
            index=0,
        )
        
        # // Define the gradient separator as a reusable component
        gradient_separator = """
            <div style="
                padding: 1.5px 0;
                background: linear-gradient(90deg, #FF4B4B 0%, rgba(255,75,75,0.2) 100%);
                margin: 20px 0;
                border-radius: 2px;
            "></div>
        """
        
        # // After City Selection Section
        st.markdown(gradient_separator, unsafe_allow_html=True)
        
        # // Update LocationService when city changes
        if 'current_city' not in st.session_state or st.session_state['current_city'] != selected_city:
            st.session_state['location_service'].set_city(selected_city)
            st.session_state['current_city'] = selected_city
            if 'listings' in st.session_state:
                del st.session_state['listings']
                if 'map' in st.session_state:
                    del st.session_state['map']

        # // Scraping Mode Section
        st.markdown('<p class="sidebar-subheader">🔄 Scraping Mode</p>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
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
        
        # // After Scraping Mode Section
        st.markdown(gradient_separator, unsafe_allow_html=True)
        
        # // Property Filters Section
        st.markdown('<p class="sidebar-subheader">🏠 Property Filters</p>', unsafe_allow_html=True)
        with st.expander("Show Filters", expanded=True):
            # // Currency selection for price input
            price_currency = st.radio(
                "💰 Price Currency",
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
        
        # // After Property Filters Section
        st.markdown(gradient_separator, unsafe_allow_html=True)
        
        # // Sort Options Section
        st.markdown('<p class="sidebar-subheader">📊 Sort Properties</p>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
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
        
        # // After Sort Options Section
        st.markdown(gradient_separator, unsafe_allow_html=True)
        
        # // Reference Locations Section
        st.markdown('<p class="sidebar-subheader">📍 Reference Locations</p>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # // Add new reference point
        with st.expander("Add New Location", expanded=False):
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
        for name, coords in st.session_state['location_service'].reference_points.items():
            st.markdown('<div class="reference-point">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📍 {name}")
            with col2:
                # // Smaller delete icon
                if st.button("🗑️", key=f"remove_{name}", help="Delete reference point"):
                    st.markdown("""
                        <style>
                            button[kind="secondary"] {
                                padding: 0px 8px !important;
                                font-size: 12px !important;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    if st.session_state['location_service'].remove_reference_point(name):
                        if not st.session_state['location_service'].reference_points:
                            st.session_state['location_service'].reset_to_defaults()
                        if 'listings' in st.session_state:
                            with st.spinner('Updating distances...'):
                                for listing in st.session_state['listings']:
                                    st.session_state['location_service'].get_location_details(listing)
                                st.session_state['map'] = create_map(st.session_state['listings'])
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Reset to Default Points"):
            st.session_state['location_service'].reset_to_defaults()
            if 'listings' in st.session_state:
                with st.spinner('Updating distances...'):
                    for listing in st.session_state['listings']:
                        st.session_state['location_service'].get_location_details(listing)
                    st.session_state['map'] = create_map(st.session_state['listings'])
            st.rerun()
            
        # // After Reference Locations Section
        st.markdown(gradient_separator, unsafe_allow_html=True)
        
        # // Currency Exchange Section
        st.markdown('<p class="sidebar-subheader">💱 Currency Exchange</p>', unsafe_allow_html=True)
        
        # // Custom CSS for inline button
        st.markdown("""
            <style>
                /* Make button more compact and inline */
                [data-testid="stHorizontalBlock"] {
                    gap: 0rem !important;
                    align-items: center !important;
                }
                button[kind="secondary"] {
                    padding: 0px 8px !important;
                    font-size: 12px !important;
                    height: 25px !important;
                    margin-left: 5px !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # // Currency rate and refresh button in one line
        cols = st.columns([0.85, 0.15])
        with cols[0]:
            st.write(f"1 THB = {st.session_state['currency_service'].thb_to_pln_rate:.4f} PLN")
        with cols[1]:
            refresh = st.button("🔄", help="Refresh exchange rate")
        
        # // Last update info
        last_update = st.session_state['currency_service'].get_last_update_time()
        if last_update:
            st.write(f"Last updated: {last_update}")
        
        # // Show success/error message under everything
        if refresh:
            rate, error = st.session_state['currency_service'].get_current_rate()
            if error:
                st.error(error)
            else:
                st.success(f"Updated from NBP: 1 THB = {rate:.4f} PLN")
                if 'listings' in st.session_state:
                    for listing in st.session_state['listings']:
                        listing.price_pln = st.session_state['currency_service'].convert_to_pln(listing.price)
                    st.rerun()
        
        # // Search Button (without gradient separator)
        st.markdown('<div class="search-button">', unsafe_allow_html=True)
        if st.button("🔍 Search Properties", use_container_width=True):
            # // Prepare search parameters with THB values
            search_params = {
                "city": selected_city,
                "region_code": CITIES[selected_city],
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
            
            with st.spinner('Fetching properties...'):
                listings = scrape_listings(max_pages, search_params)
                if listings:
                    st.session_state['listings'] = listings
                    st.session_state['map'] = create_map(listings)
                    st.success(f'Found {len(listings)} properties!')
                else:
                    st.error("No properties found. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    # // Create columns for grid layout with proper spacing
    st.markdown("""
        <style>
            [data-testid="column"] {
                padding: 0 10px;  /* Add horizontal padding between columns */
            }
            [data-testid="column"]:first-child {
                padding-left: 0;  /* Remove padding for first column */
            }
            [data-testid="column"]:last-child {
                padding-right: 0;  /* Remove padding for last column */
            }
            /* Remove vertical gaps between listings */
            div[data-testid="stVerticalBlock"] > div {
                margin-bottom: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    
    for i, listing in enumerate(sorted_listings):
        with cols[i % 3]:
            with st.container():
                st.markdown("""
                    <style>
                        div[data-testid="stVerticalBlock"] {
                            background-color: transparent !important;
                            gap: 0rem !important;
                        }
                        div.stMarkdown {
                            background-color: transparent !important;
                        }
                        .property-image {
                            width: 100%;
                            height: 200px;
                            object-fit: cover;
                            border-radius: 10px;
                            margin-bottom: 10px;
                        }
                        .property-title {
                            font-size: 16px;
                            font-weight: bold;
                            color: white;
                            margin-bottom: 10px;
                        }
                        .price-tag {
                            font-size: 18px;
                            color: #FF4B4B;
                            font-weight: bold;
                            margin: 5px 0;
                        }
                        .pln-price {
                            font-size: 14px;
                            color: #FF4B4B;
                            margin-top: -5px;
                        }
                        .property-details {
                            color: white;
                            margin: 5px 0;
                            font-size: 14px;
                        }
                        .view-button {
                            background-color: #FF4B4B;
                            color: white;
                            padding: 8px;
                            text-align: center;
                            border-radius: 5px;
                            text-decoration: none;
                            display: block;
                            margin-top: 10px;
                            font-size: 14px;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                # // Image
                if listing.property_info.image_url:
                    st.markdown(f'<img src="{listing.property_info.image_url}" class="property-image">', unsafe_allow_html=True)
                else:
                    st.markdown('<img src="https://via.placeholder.com/400x300?text=No+Image" class="property-image">', unsafe_allow_html=True)
                
                # // Title
                st.markdown(f'<div class="property-title">{listing.name}</div>', unsafe_allow_html=True)
                
                # // Price
                st.markdown(f"""
                    <div class="price-tag">฿{listing.price:,}/month</div>
                    <div class="pln-price">(~{listing.price_pln:,.2f} PLN/month)</div>
                """, unsafe_allow_html=True)
                
                # // Property details
                st.markdown(f"""
                    <div class="property-details">
                        🛏️ {listing.property_info.bedrooms} beds &nbsp;&nbsp; 
                        🚿 {listing.property_info.bathrooms} baths<br>
                        🏠 {listing.property_info.property_type} &nbsp;&nbsp; 
                        📏 {listing.property_info.floor_area}
                    </div>
                """, unsafe_allow_html=True)
                
                # // Location and distances
                st.markdown(f"""
                    <div class="property-details">
                        📍 {listing.location.area}, {listing.location.district}
                    </div>
                """, unsafe_allow_html=True)
                
                if listing.location.distances:
                    for loc_name, distance in listing.location.distances.items():
                        st.markdown(f"""
                            <div class="property-details">
                                🎯 {distance:.1f} km to {loc_name}
                            </div>
                        """, unsafe_allow_html=True)
                
                # // View button
                st.markdown(f'<a href="{listing.listing_info.url}" target="_blank" class="view-button">View Property</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
