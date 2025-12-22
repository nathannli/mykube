from datetime import datetime

WEEKDAY = "weekday"
WEEKEND = "weekend"
WINTER = "winter"
SUMMER = "summer"

class TimeOfUseElectricityPricing:
    """
    main usage function: get_current_price
    """

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

    def get_winter_pricing_date_start(self) -> datetime:
        return datetime(year=datetime.now().year, month=11, day=1)

    def get_winter_pricing_date_end(self) -> datetime:
        return datetime(year=datetime.now().year + 1, month=4, day=30)
    
    def is_winter(self) -> bool:
        return self.get_winter_pricing_date_start() <= datetime.now() <= self.get_winter_pricing_date_end()

    def is_weekday(self) -> bool:
        return datetime.now().weekday() < 5

    def get_current_price(self) -> float:
        cur_hour: int = datetime.now().hour
        season = WINTER if self.is_winter() else SUMMER
        day_type = WEEKDAY if self.is_weekday() else WEEKEND
        return self.pricing[season][day_type][cur_hour]
