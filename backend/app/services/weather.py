"""Optional live weather adapter. Failure is explicit and does not block restaurant details."""
import httpx
async def current(lat,lon):
    if lat is None or lon is None: return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r=await client.get("https://api.open-meteo.com/v1/forecast",params={"latitude":lat,"longitude":lon,
                "current":"temperature_2m,precipitation","timezone":"Europe/Berlin"})
        r.raise_for_status()
        return r.json().get("current")
    except (httpx.HTTPError,ValueError):
        return None
