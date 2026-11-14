import httpx

from config import settings


async def get_weather(city: str) -> str:
    if not settings.WEATHER_API_KEY:
        return "Error: WEATHER_API_KEY is not configured"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": settings.WEATHER_API_KEY, "units": "metric"},
            )
        data = resp.json()
        if resp.status_code != 200:
            return f"Error: {data.get('message', 'weather lookup failed')}"
        return (
            f"{city}: {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C), "
            f"{data['weather'][0]['description']}, humidity {data['main']['humidity']}%, "
            f"wind {data['wind']['speed']} m/s"
        )
    except Exception as e:
        return f"Error: weather lookup failed ({type(e).__name__}: {e})"
