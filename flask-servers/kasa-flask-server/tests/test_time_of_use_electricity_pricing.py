"""
Tests for TimeOfUseElectricityPricing class.

Tests cover:
- Pricing dictionary structure and values
- Winter/summer season detection
- Weekday/weekend detection
- Current price calculation with various datetime scenarios
- All times are in Toronto timezone (EST/EDT)
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import sys
from pathlib import Path

# Add docker-app directory to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / 'docker-app'))

from time_of_use_electricity_pricing import (
    TimeOfUseElectricityPricing,
    WEEKDAY,
    WEEKEND,
    WINTER,
    SUMMER,
)

# Toronto timezone
TORONTO_TZ = ZoneInfo('America/Toronto')


def make_toronto_datetime(year, month, day, hour=0, minute=0, second=0):
    """Helper function to create timezone-aware datetime in Toronto timezone."""
    return datetime(year, month, day, hour, minute, second, tzinfo=TORONTO_TZ)


class TestPricingStructure:
    """Test the pricing dictionary structure and values."""

    def test_pricing_dict_has_both_seasons(self):
        """Test that pricing includes both winter and summer."""
        pricing = TimeOfUseElectricityPricing.pricing
        assert WINTER in pricing
        assert SUMMER in pricing

    def test_each_season_has_both_day_types(self):
        """Test that each season has weekday and weekend rates."""
        pricing = TimeOfUseElectricityPricing.pricing
        for season in [WINTER, SUMMER]:
            assert WEEKDAY in pricing[season]
            assert WEEKEND in pricing[season]

    def test_each_day_type_has_all_hours(self):
        """Test that each day type has rates for all 24 hours."""
        pricing = TimeOfUseElectricityPricing.pricing
        for season in [WINTER, SUMMER]:
            for day_type in [WEEKDAY, WEEKEND]:
                hours = pricing[season][day_type]
                assert len(hours) == 24
                assert set(hours.keys()) == set(range(24))

    def test_all_prices_are_positive_floats(self):
        """Test that all pricing rates are positive floats."""
        pricing = TimeOfUseElectricityPricing.pricing
        for season in [WINTER, SUMMER]:
            for day_type in [WEEKDAY, WEEKEND]:
                for hour, price in pricing[season][day_type].items():
                    assert isinstance(price, float)
                    assert price > 0

    def test_winter_weekday_pricing(self):
        """Test specific winter weekday pricing values."""
        pricing = TimeOfUseElectricityPricing.pricing[WINTER][WEEKDAY]
        # 0-6: 0.098
        for h in range(0, 7):
            assert pricing[h] == 0.098
        # 7-10: 0.203
        for h in range(7, 11):
            assert pricing[h] == 0.203
        # 11-16: 0.157
        for h in range(11, 17):
            assert pricing[h] == 0.157
        # 17-18: 0.203
        for h in range(17, 19):
            assert pricing[h] == 0.203
        # 19-23: 0.098
        for h in range(19, 24):
            assert pricing[h] == 0.098

    def test_winter_weekend_pricing(self):
        """Test that winter weekends have flat rate."""
        pricing = TimeOfUseElectricityPricing.pricing[WINTER][WEEKEND]
        for h in range(24):
            assert pricing[h] == 0.098

    def test_summer_weekday_pricing(self):
        """Test specific summer weekday pricing values."""
        pricing = TimeOfUseElectricityPricing.pricing[SUMMER][WEEKDAY]
        # 0-6: 0.076
        for h in range(0, 7):
            assert pricing[h] == 0.076
        # 7-10: 0.122
        for h in range(7, 11):
            assert pricing[h] == 0.122
        # 11-16: 0.158
        for h in range(11, 17):
            assert pricing[h] == 0.158
        # 17-18: 0.122
        for h in range(17, 19):
            assert pricing[h] == 0.122
        # 19-23: 0.076
        for h in range(19, 24):
            assert pricing[h] == 0.076

    def test_summer_weekend_pricing(self):
        """Test that summer weekends have flat rate."""
        pricing = TimeOfUseElectricityPricing.pricing[SUMMER][WEEKEND]
        for h in range(24):
            assert pricing[h] == 0.076


class TestWinterDateRange:
    """Test winter date range calculations.

    Winter pricing runs from Nov 1 to Apr 30 (spanning two calendar years).
    The date range calculation depends on the current month:
    - Jan-Apr: winter started last Nov, ends this Apr
    - May-Oct: next winter starts this Nov, ends next Apr
    - Nov-Dec: winter started this Nov, ends next Apr
    """

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_start_date_when_in_january(self, mock_datetime):
        """Test winter start date when current date is in January."""
        # January 15, 2026 -> winter started Nov 1, 2025
        mock_now = make_toronto_datetime(2026, 1, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        start = pricing.get_winter_pricing_date_start()
        assert start.month == 11
        assert start.day == 1
        assert start.year == 2025  # Previous year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_end_date_when_in_january(self, mock_datetime):
        """Test winter end date when current date is in January."""
        # January 15, 2026 -> winter ends Apr 30, 2026
        mock_now = make_toronto_datetime(2026, 1, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        end = pricing.get_winter_pricing_date_end()
        assert end.month == 4
        assert end.day == 30
        assert end.year == 2026  # Current year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_start_date_when_in_june(self, mock_datetime):
        """Test winter start date when current date is in June (summer)."""
        # June 15, 2026 -> next winter starts Nov 1, 2026
        mock_now = make_toronto_datetime(2026, 6, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        start = pricing.get_winter_pricing_date_start()
        assert start.month == 11
        assert start.day == 1
        assert start.year == 2026  # Current year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_end_date_when_in_june(self, mock_datetime):
        """Test winter end date when current date is in June (summer)."""
        # June 15, 2026 -> next winter ends Apr 30, 2027
        mock_now = make_toronto_datetime(2026, 6, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        end = pricing.get_winter_pricing_date_end()
        assert end.month == 4
        assert end.day == 30
        assert end.year == 2027  # Next year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_start_date_when_in_november(self, mock_datetime):
        """Test winter start date when current date is in November."""
        # November 15, 2025 -> winter started Nov 1, 2025
        mock_now = make_toronto_datetime(2025, 11, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        start = pricing.get_winter_pricing_date_start()
        assert start.month == 11
        assert start.day == 1
        assert start.year == 2025  # Current year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_end_date_when_in_november(self, mock_datetime):
        """Test winter end date when current date is in November."""
        # November 15, 2025 -> winter ends Apr 30, 2026
        mock_now = make_toronto_datetime(2025, 11, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        end = pricing.get_winter_pricing_date_end()
        assert end.month == 4
        assert end.day == 30
        assert end.year == 2026  # Next year

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_on_jan_2_2026(self, mock_datetime):
        """Test is_winter returns True on January 2, 2026 (the reported bug scenario)."""
        # January 2, 2026 should be in winter (Nov 1, 2025 - Apr 30, 2026)
        mock_now = make_toronto_datetime(2026, 1, 2, 12)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_during_november(self, mock_datetime):
        """Test is_winter returns True during November (Toronto timezone EST)."""
        # November 15, 2025 - clearly in winter season
        mock_now = make_toronto_datetime(2025, 11, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_during_december(self, mock_datetime):
        """Test is_winter returns True during December (Toronto timezone EST)."""
        # December 15, 2025 - clearly in winter season
        mock_now = make_toronto_datetime(2025, 12, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_during_january(self, mock_datetime):
        """Test is_winter returns True during January (Toronto timezone EST)."""
        # January 15, 2026 - should be in winter (Nov 2025 - Apr 2026)
        mock_now = make_toronto_datetime(2026, 1, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_during_april(self, mock_datetime):
        """Test is_winter returns True during April (Toronto timezone EST)."""
        # April 15, 2026 - should be in winter (Nov 2025 - Apr 2026)
        mock_now = make_toronto_datetime(2026, 4, 15, 12)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_at_boundary_start(self, mock_datetime):
        """Test is_winter returns True on November 1 (Toronto timezone EST)."""
        # November 1 at midnight Toronto time
        mock_now = make_toronto_datetime(2025, 11, 1, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_winter_at_boundary_end(self, mock_datetime):
        """Test is_winter returns True on April 30 (Toronto timezone EST)."""
        # April 30 at 11:59 PM Toronto time
        mock_now = make_toronto_datetime(2026, 4, 30, 23, 59, 59)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_not_winter_in_summer(self, mock_datetime):
        """Test is_winter returns False during summer (Toronto timezone EDT)."""
        # June 15
        mock_now = make_toronto_datetime(2026, 6, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is False

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_not_winter_after_april_30(self, mock_datetime):
        """Test is_winter returns False on May 1 (Toronto timezone EDT)."""
        # May 1
        mock_now = make_toronto_datetime(2026, 5, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is False

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_not_winter_before_november_1(self, mock_datetime):
        """Test is_winter returns False on October 31 (Toronto timezone EDT)."""
        # October 31
        mock_now = make_toronto_datetime(2025, 10, 31)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_winter() is False


class TestWeekdayDetection:
    """Test weekday vs weekend detection (Toronto timezone)."""

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_weekday_on_monday(self, mock_datetime):
        """Test is_weekday returns True on Monday (Toronto timezone EST)."""
        # Monday, January 1, 2024 (times implicitly in Toronto EST)
        mock_datetime.now.return_value = make_toronto_datetime(2024, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_weekday() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_weekday_on_wednesday(self, mock_datetime):
        """Test is_weekday returns True on Wednesday (Toronto timezone EST)."""
        # Wednesday, January 3, 2024 (times implicitly in Toronto EST)
        mock_datetime.now.return_value = make_toronto_datetime(2024, 1, 3)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_weekday() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_weekday_on_friday(self, mock_datetime):
        """Test is_weekday returns True on Friday (Toronto timezone EST)."""
        # Friday, January 5, 2024 (times implicitly in Toronto EST)
        mock_datetime.now.return_value = make_toronto_datetime(2024, 1, 5)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_weekday() is True

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_not_weekday_on_saturday(self, mock_datetime):
        """Test is_weekday returns False on Saturday (Toronto timezone EST)."""
        # Saturday, January 6, 2024 (times implicitly in Toronto EST)
        mock_datetime.now.return_value = make_toronto_datetime(2024, 1, 6)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_weekday() is False

    @patch('time_of_use_electricity_pricing.datetime')
    def test_is_not_weekday_on_sunday(self, mock_datetime):
        """Test is_weekday returns False on Sunday (Toronto timezone EST)."""
        # Sunday, January 7, 2024 (times implicitly in Toronto EST)
        mock_datetime.now.return_value = make_toronto_datetime(2024, 1, 7)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.is_weekday() is False


class TestGetCurrentPrice:
    """Test get_current_price method with various scenarios (Toronto timezone)."""

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekday_off_peak_morning(self, mock_datetime):
        """Test winter weekday off-peak morning rate (Toronto timezone EST)."""
        # Monday, November 10, 6:00 AM (winter, weekday, hour 6, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 10, 6, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.098

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekday_peak_morning(self, mock_datetime):
        """Test winter weekday peak morning rate 7-10 (Toronto timezone EST)."""
        # Monday, November 10, 9:00 AM (winter, weekday, hour 9, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 10, 9, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.203

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekday_partial_peak_afternoon(self, mock_datetime):
        """Test winter weekday partial peak afternoon rate 11-16 (Toronto timezone EST)."""
        # Monday, November 10, 2:00 PM (winter, weekday, hour 14, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 10, 14, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.157

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekday_peak_evening(self, mock_datetime):
        """Test winter weekday peak evening rate 17-18 (Toronto timezone EST)."""
        # Monday, November 10, 5:00 PM (winter, weekday, hour 17, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 10, 17, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.203

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekday_off_peak_night(self, mock_datetime):
        """Test winter weekday off-peak night rate (Toronto timezone EST)."""
        # Monday, November 10, 10:00 PM (winter, weekday, hour 22, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 10, 22, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.098

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekend_flat_rate(self, mock_datetime):
        """Test winter weekend has flat rate all day (Toronto timezone EST)."""
        # Saturday, November 8, 2:00 PM (winter, weekend, hour 14, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 8, 14, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.098

    @patch('time_of_use_electricity_pricing.datetime')
    def test_winter_weekend_flat_rate_midnight(self, mock_datetime):
        """Test winter weekend flat rate at midnight (Toronto timezone EST)."""
        # Saturday, November 8, 12:00 AM (winter, weekend, hour 0, times implicitly EST)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 11, 8, 0, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.098

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekday_off_peak_morning(self, mock_datetime):
        """Test summer weekday off-peak morning rate (Toronto timezone EDT)."""
        # Monday, June 10, 6:00 AM (summer, weekday, hour 6, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 10, 6, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.076

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekday_peak_morning(self, mock_datetime):
        """Test summer weekday peak morning rate 7-10 (Toronto timezone EDT)."""
        # Monday, June 10, 8:00 AM (summer, weekday, hour 8, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 10, 8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.122

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekday_peak_afternoon(self, mock_datetime):
        """Test summer weekday peak afternoon rate 11-16 (Toronto timezone EDT)."""
        # Monday, June 10, 1:00 PM (summer, weekday, hour 13, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 10, 13, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.158

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekday_partial_peak_evening(self, mock_datetime):
        """Test summer weekday partial peak evening rate 17-18 (Toronto timezone EDT)."""
        # Monday, June 10, 6:00 PM (summer, weekday, hour 18, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 10, 18, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.122

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekday_off_peak_night(self, mock_datetime):
        """Test summer weekday off-peak night rate (Toronto timezone EDT)."""
        # Monday, June 10, 11:00 PM (summer, weekday, hour 23, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 10, 23, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.076

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekend_flat_rate(self, mock_datetime):
        """Test summer weekend has flat rate all day (Toronto timezone EDT)."""
        # Sunday, June 7, 2:00 PM (summer, weekend, hour 14, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 7, 14, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.076

    @patch('time_of_use_electricity_pricing.datetime')
    def test_summer_weekend_flat_rate_evening(self, mock_datetime):
        """Test summer weekend flat rate in evening (Toronto timezone EDT)."""
        # Sunday, June 7, 8:00 PM (summer, weekend, hour 20, times implicitly EDT)
        current_year = datetime.now(TORONTO_TZ).year
        mock_now = make_toronto_datetime(current_year, 6, 7, 20, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()
        assert pricing.get_current_price() == 0.076

    @patch('time_of_use_electricity_pricing.datetime')
    def test_transition_from_summer_to_winter(self, mock_datetime):
        """Test transition from summer to winter pricing (Toronto timezone)."""
        # October 20 (summer) vs November 20 (winter) - both guaranteed to be weekdays
        # Times implicitly in Toronto EDT/EST
        current_year = datetime.now(TORONTO_TZ).year
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()

        mock_datetime.now.return_value = make_toronto_datetime(current_year, 10, 20, 9, 0, 0)
        oct_20_price = pricing.get_current_price()

        mock_datetime.now.return_value = make_toronto_datetime(current_year, 11, 20, 9, 0, 0)
        nov_20_price = pricing.get_current_price()

        # October 20 should be summer peak: 0.122 (weekday, EDT)
        assert oct_20_price == 0.122
        # November 20 should be winter weekday peak: 0.203 (weekday, EST)
        assert nov_20_price == 0.203
        # Prices should differ between summer and winter
        assert oct_20_price != nov_20_price

    @patch('time_of_use_electricity_pricing.datetime')
    def test_transition_from_winter_to_summer(self, mock_datetime):
        """Test transition from winter to summer pricing (Toronto timezone)."""
        # April 20 (winter) vs May 20 (summer) - both are weekdays
        # Times implicitly in Toronto EST/EDT
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()

        # April 20, 2026 should be in winter (Nov 2025 - Apr 2026)
        mock_datetime.now.return_value = make_toronto_datetime(2026, 4, 20, 9, 0, 0)
        apr_20_price = pricing.get_current_price()

        # May 20, 2026 should be in summer (May 2026 - Oct 2026)
        mock_datetime.now.return_value = make_toronto_datetime(2026, 5, 20, 9, 0, 0)
        may_20_price = pricing.get_current_price()

        # April 20 should be winter peak: 0.203 (weekday, hour 9, EST)
        assert apr_20_price == 0.203
        # May 20 should be summer peak: 0.122 (weekday, hour 9, EDT)
        assert may_20_price == 0.122
        # Prices should differ between winter and summer
        assert apr_20_price != may_20_price

    @patch('time_of_use_electricity_pricing.datetime')
    def test_price_dec_22_2025(self, mock_datetime):
        """Test pricing on specific date Dec 22, 2025 (Toronto timezone EST)."""
        # December 22, 2025 at 2:00 PM (times implicitly in Toronto EST)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        pricing = TimeOfUseElectricityPricing()

        # December 22, 2025 is a Monday
        mock_datetime.now.return_value = make_toronto_datetime(year=2025, month=12, day=22, hour=14)
        dec_22_2025_price = pricing.get_current_price()

        # Hour 14 (2:00 PM) in winter weekday: partial peak (11-16) = 0.157
        assert dec_22_2025_price == 0.157
