from zoneinfo import ZoneInfo
from datetime import datetime

WEEKDAY = "weekday"
WEEKEND = "weekend"
WINTER = "winter"
SUMMER = "summer"

HOLIDAY_DATES = [
    # 2025
    datetime(year=2025, month=12, day=25, tzinfo=ZoneInfo("America/Toronto")),  # Christmas Day
    datetime(year=2025, month=12, day=26, tzinfo=ZoneInfo("America/Toronto")),  # Boxing Day
    # 2026
    datetime(year=2026, month=1, day=1, tzinfo=ZoneInfo("America/Toronto")),    # New Year's Day
    datetime(year=2026, month=2, day=16, tzinfo=ZoneInfo("America/Toronto")),   # Family Day
    datetime(year=2026, month=4, day=3, tzinfo=ZoneInfo("America/Toronto")),    # Good Friday
    datetime(year=2026, month=5, day=18, tzinfo=ZoneInfo("America/Toronto")),   # Victoria Day
    datetime(year=2026, month=7, day=1, tzinfo=ZoneInfo("America/Toronto")),    # Canada Day
    datetime(year=2026, month=8, day=3, tzinfo=ZoneInfo("America/Toronto")),    # Civic Holiday
    datetime(year=2026, month=9, day=7, tzinfo=ZoneInfo("America/Toronto")),    # Labour Day
    datetime(year=2026, month=10, day=12, tzinfo=ZoneInfo("America/Toronto")),  # Thanksgiving Day
    datetime(year=2026, month=12, day=25, tzinfo=ZoneInfo("America/Toronto")),  # Christmas Day
    datetime(year=2026, month=12, day=28, tzinfo=ZoneInfo("America/Toronto")),  # Boxing Day
]

class TimeOfUseElectricityPricing:
    """
    main usage function: get_current_price
    """

    toronto_tz = ZoneInfo("America/Toronto")

    pricing: dict[str, dict[str, dict[int, float]]] = {
        WINTER: {
            WEEKDAY: {
                **{h: 0.098 for h in range(0, 7)},
                **{h: 0.203 for h in range(7, 11)},
                **{h: 0.157 for h in range(11, 17)},
                **{h: 0.203 for h in range(17, 19)},
                **{h: 0.098 for h in range(19, 24)},
            },
            WEEKEND: {h: 0.098 for h in range(24)}
        },
        SUMMER: {
            WEEKDAY: {
                **{h: 0.076 for h in range(0, 7)},
                **{h: 0.122 for h in range(7, 11)},
                **{h: 0.158 for h in range(11, 17)},
                **{h: 0.122 for h in range(17, 19)},
                **{h: 0.076 for h in range(19, 24)},
            },
            WEEKEND: {h: 0.076 for h in range(24)},
        }
    }

    def get_now(self):
        return datetime.now(tz=self.toronto_tz)

    def get_winter_pricing_date_start(self) -> datetime:
        return datetime(year=self.get_now().year, month=11, day=1, tzinfo=self.toronto_tz)

    def get_winter_pricing_date_end(self) -> datetime:
        return datetime(year=self.get_now().year + 1, month=4, day=30, tzinfo=self.toronto_tz)

    def is_winter(self) -> bool:
        return self.get_winter_pricing_date_start() <= self.get_now() <= self.get_winter_pricing_date_end()

    def is_weekday(self) -> bool:
        return self.get_now().weekday() < 5

    def get_current_price(self) -> float:
        cur_hour: int = self.get_now().hour
        season = WINTER if self.is_winter() else SUMMER
        day_type = WEEKDAY if self.is_weekday() and self.get_now() not in HOLIDAY_DATES else WEEKEND
        return self.pricing[season][day_type][cur_hour]

    def __repr__(self):
        cur_hour: int = self.get_now().hour
        season = WINTER if self.is_winter() else SUMMER
        day_type = WEEKDAY if self.is_weekday() else WEEKEND
        str_builder = f"""
            get_winter_pricing_date_start: {self.get_winter_pricing_date_start()}
            get_winter_pricing_date_end: {self.get_winter_pricing_date_end()}
            is_winter: {self.is_winter()}
            is_weekday: {self.is_weekday()}
            season: {season}
            date_type: {day_type}
            cur_hour: {cur_hour}
            get_current_price: {self.get_current_price()}
        """
        return str_builder

