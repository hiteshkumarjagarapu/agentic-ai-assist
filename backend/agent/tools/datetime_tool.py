from datetime import datetime

import pytz


async def get_datetime(timezone: str = "Asia/Kolkata") -> str:
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return (
            f"Current date: {now.strftime('%Y-%m-%d')}, Time: {now.strftime('%H:%M:%S')}, "
            f"Timezone: {timezone}"
        )
    except pytz.UnknownTimeZoneError:
        return f"Error: unknown timezone '{timezone}'"
    except Exception as e:
        return f"Error: {e}"
