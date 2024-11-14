import streamlit as st
from dd_property_scraper import DDPropertyScraper
from location_service import LocationService
import folium
from streamlit_folium import st_folium
from typing import List
from models import PropertyListing

def scrape_listings(max_pages: int = None) -> List[PropertyListing]:
    """
    // Pobiera ogłoszenia z DD Property
    """
    scraper = DDPropertyScraper()
    location_service = LocationService()
    
    base_url = f"{scraper.base_url}/en/property-for-rent?region_code=TH83&freetext=Phuket&beds[]=2&listing_type=rent&maxprice=25000&market=residential&search=true"
    listings = scraper.scrape_all_pages(base_url, max_pages=max_pages)
    
    # // Dodaj informacje o lokalizacji
    for listing in listings:
        location_service.get_location_details(listing)
    
    return listings

def create_map(listings: List[PropertyListing]):
    """
    // Tworzy mapę z zaznaczonymi lokalizacjami, grupując oferty w tych samych lokalizacjach
    """
    # // Centrum Phuket
    m = folium.Map(location=[7.9519, 98.3381], zoom_start=11)
    
    # // Dodaj Patong Beach jako punkt referencyjny
    folium.Marker(
        [7.9039, 98.2970],
        popup="Patong Beach",
        icon=folium.Icon(color='red', icon='info-sign')
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
                </style>
                <div class="popup-container">
                    <div class="location-header">
                        <h4>{area} - {len(listings)} properties</h4>
                    </div>
        """
        
        for listing in listings:
            popup_html += f"""
                <div class="property-card">
                    <div class="property-title">{listing.name}</div>
                    <div class="property-price">฿{listing.price:,}/month</div>
                    <div class="property-details">
                        {listing.property_info.bedrooms} bed, {listing.property_info.bathrooms} bath<br>
                        Size: {listing.property_info.floor_area}
                    </div>
                    <a href="{listing.listing_info.url}" target="_blank" class="view-button">
                        View Property
                    </a>
                </div>
            """
        
        popup_html += "</div></div>"
        
        # // Twórz marker z ikoną pokazującą liczbę ofert
        icon = None
        if len(listings) > 1:
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
        else:
            icon = folium.Icon(color='blue')
        
        # // Dodaj marker do mapy z większym popupem
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=300, max_height=500),  # Increased max_height
            tooltip=f"{area} - {len(listings)} properties",
            icon=icon
        ).add_to(m)
    
    return m

def main():
    st.set_page_config(
        page_title="DD Property Listings",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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
        </style>
    """, unsafe_allow_html=True)
    
    st.title("DD Property Listings in Phuket 🌴")
    
    # // Sidebar controls
    with st.sidebar:
        st.header("Search Settings")
        max_pages = st.number_input("Number of pages to scrape", min_value=1, value=1)
        
        with st.expander("About", expanded=True):
            st.markdown("""
                This app shows available properties in Phuket with:
                - 2 bedrooms
                - Max price: ฿25,000/month
                - Distance to Patong Beach
            """)
            
        if st.button("🔍 Search Properties", use_container_width=True):
            with st.spinner('Fetching properties...'):
                listings = scrape_listings(max_pages)
                st.session_state['listings'] = listings
                st.session_state['map'] = create_map(listings)
            st.success(f'Found {len(listings)} properties!')
    
    # // Main content
    if 'listings' not in st.session_state:
        st.info("👈 Set your search parameters and click 'Search Properties' to start")
        return
    
    # // Display map
    st.subheader("📍 Property Locations")
    st_folium(st.session_state['map'], use_container_width=True, height=600)
    
    # // Display listings in grid
    st.subheader("🏠 Available Properties")
    
    # // Create columns for grid layout
    cols = st.columns(3)
    
    for i, listing in enumerate(st.session_state['listings']):
        with cols[i % 3]:
            with st.container():
                st.markdown('<div class="listing-card">', unsafe_allow_html=True)
                
                # // Image
                if listing.property_info.image_url:
                    st.image(listing.property_info.image_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/400x300?text=No+Image", use_container_width=True)
                
                # // Basic info
                st.markdown(f"### {listing.name}")
                st.markdown(f'<p class="price-tag">฿{listing.price:,}/month</p>', unsafe_allow_html=True)
                
                # // Property details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🛏️ {listing.property_info.bedrooms} beds")
                    st.write(f"🏠 {listing.property_info.property_type}")
                with col2:
                    st.write(f"🚿 {listing.property_info.bathrooms} baths")
                    st.write(f"📏 {listing.property_info.floor_area}")
                
                # // Location info
                st.markdown("#### 📍 Location")
                st.write(f"{listing.location.area}, {listing.location.district}")
                if listing.location.distance_to_patong is not None:
                    st.write(f"🏖️ {listing.location.distance_to_patong:.1f} km to Patong")
                
                # // Agent info
                with st.expander("👤 Agent Details"):
                    st.write(f"Name: {listing.agent_info.name}")
                    st.write(f"Phone: {listing.agent_info.phone_formatted}")
                    if listing.agent_info.line_id:
                        st.write(f"LINE: {listing.agent_info.line_id}")
                    if listing.agent_info.is_verified:
                        st.write("✅ Verified Agent")
                
                # // View listing button
                st.markdown(f'<a href="{listing.listing_info.url}" target="_blank"><button style="width:100%; padding:10px; background-color:#FF4B4B; color:white; border:none; border-radius:5px; cursor:pointer;">View Property</button></a>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
