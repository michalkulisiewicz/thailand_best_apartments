from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Location:
    district: Optional[str] = None
    region: Optional[str] = None
    area: Optional[str] = None
    district_code: Optional[str] = None
    region_code: Optional[str] = None
    area_code: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None
    distance_to_patong: Optional[float] = None
    address: Optional[str] = None

@dataclass
class PropertyInfo:
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor_area: Optional[str] = None
    property_type: Optional[str] = None
    furnishing: Optional[str] = None
    image_url: Optional[str] = None

@dataclass
class ListingInfo:
    id: Optional[str] = None
    url: Optional[str] = None
    position: Optional[int] = None
    status: Optional[str] = None
    variant: Optional[str] = None

@dataclass
class AgentInfo:
    id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    phone_formatted: Optional[str] = None
    line_id: Optional[str] = None
    is_verified: bool = False
    verification_date: Optional[str] = None
    agency_type: Optional[str] = None
    profile_image: Optional[str] = None

@dataclass
class PropertyListing:
    name: Optional[str] = None
    price: Optional[int] = None
    location: Location = None
    property_info: PropertyInfo = None
    listing_info: ListingInfo = None
    agent_info: AgentInfo = None

    def __post_init__(self):
        if self.location is None:
            self.location = Location()
        if self.property_info is None:
            self.property_info = PropertyInfo()
        if self.listing_info is None:
            self.listing_info = ListingInfo()
        if self.agent_info is None:
            self.agent_info = AgentInfo() 
