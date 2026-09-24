"""Google-specific data stays behind this adapter; no persistent Places content cache."""
import os
import httpx

class ServiceError(Exception):
    def __init__(self, message, status=502):
        self.message, self.status = message, status

BASE = "https://places.googleapis.com/v1/places"
FIELDS = "id,displayName,formattedAddress,location,googleMapsUri,businessStatus,attributions"
DETAIL_FIELDS = FIELDS + ",rating,userRatingCount,websiteUri,nationalPhoneNumber,currentOpeningHours,priceLevel,editorialSummary"

def normalize(p):
    loc = p.get("location", {})
    return {"id":p["id"], "name":p.get("displayName",{}).get("text","Restaurant"),
        "address":p.get("formattedAddress",""), "lat":loc.get("latitude"),"lon":loc.get("longitude"),
        "maps_url":p.get("googleMapsUri"),"website":p.get("websiteUri"),
        "rating":p.get("rating"),"rating_count":p.get("userRatingCount"),
        "phone":p.get("nationalPhoneNumber"),"open_now":p.get("currentOpeningHours",{}).get("openNow"),
        "hours":p.get("currentOpeningHours",{}).get("weekdayDescriptions",[]),
        "summary":p.get("editorialSummary",{}).get("text"),
        "business_status":p.get("businessStatus"),"attributions":p.get("attributions",[])}

def in_berlin(p):
    lat,lon=p.get("lat"),p.get("lon")
    return lat is not None and lon is not None and 52.33 <= lat <= 52.68 and 13.08 <= lon <= 13.77

async def request(method, suffix, fields, body=None):
    key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not key:
        raise ServiceError("Restaurant search is not connected yet. Add the Google Places key to the server configuration.",503)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, BASE+suffix, headers={"X-Goog-Api-Key":key,"X-Goog-FieldMask":fields},json=body)
        if response.status_code in (401,403):
            raise ServiceError("Google Places rejected access. Check the server key, API restrictions and billing.",503)
        if response.status_code == 429:
            raise ServiceError("Restaurant search has reached its provider limit. Please try later.",429)
        if response.status_code == 404:
            raise ServiceError("This restaurant could not be found.",404)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ServiceError("Restaurant search is temporarily unavailable. Please try again.") from exc

async def search(query):
    raw = await request("POST",":searchText",','.join('places.'+f for f in FIELDS.split(',')),
        {"textQuery":query+" in Berlin, Germany", "includedType":"restaurant","strictTypeFiltering":True,
         "languageCode":"en","pageSize":8,"locationRestriction":{"rectangle":{
         "low":{"latitude":52.33,"longitude":13.08},"high":{"latitude":52.68,"longitude":13.77}}}})
    return [p for p in map(normalize,raw.get("places",[])) if in_berlin(p)]

async def details(place_id):
    p=normalize(await request("GET","/"+place_id+"?languageCode=en",DETAIL_FIELDS))
    if not in_berlin(p):
        raise ServiceError("Please choose a restaurant within the Berlin search area.",422)
    return p
