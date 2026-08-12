# AI Context Pack

## User task

Fix Kasa exporter so one KP125M device protocol failure does not remove successfully collected KP125M metrics from /metrics

## Relevant files

### argononerpi4case/case-fan-install.md
Reason: Keyword match (score: 1.50)

### flask-servers/kasa-flask-server/docker-app/config.py
Reason: Keyword match (score: 0.50)
Important symbols:
- Config L20-54 - class Config
- get_bool_env L13-17 - def get_bool_env
- require_env L6-10 - def require_env

### flask-servers/kasa-flask-server/docker-app/flask-app.py
Reason: Keyword match (score: 1.50)
Important symbols:
- connect_to_kp125m_device L87-99 - def connect_to_kp125m_device
- get_metrics_KP125M L209-229 - def get_metrics_KP125M
- check_all_desktop_plugs_are_off_KP125M L175-185 - def check_all_desktop_plugs_are_off_KP125M
- connect_to_device L63-84 - def connect_to_device
- connect_to_hs300_device L102-107 - def connect_to_hs300_device
- get_metrics_HS300 L120-134 - def get_metrics_HS300
- log_device_error L58-60 - def log_device_error
- turn_off_desktop_plugs_if_no_power_KP125M L188-206 - def turn_off_desktop_plugs_if_no_power_KP125M

### flask-servers/kasa-flask-server/docker-app/my_logger.py
Reason: Keyword match (score: 0.50)
Important symbols:
- Logger L8-41 - class Logger

### flask-servers/kasa-flask-server/docker-app/pyproject.toml
Reason: Keyword match (score: 1.50)

### flask-servers/kasa-flask-server/docker-app/tester.py
Reason: Keyword match (score: 0.50)
Important symbols:
- main L9-14 - def main

### flask-servers/kasa-flask-server/docker-app/time_of_use_electricity_pricing.py
Reason: Keyword match (score: 1.50)
Important symbols:
- TimeOfUseElectricityPricing L26-101 - class TimeOfUseElectricityPricing

### flask-servers/kasa-flask-server/kube-configs/config_map.yml
Reason: Keyword match (score: 1.50)

### flask-servers/kasa-flask-server/kube-configs/deployment.yml
Reason: Keyword match (score: 1.50)

### flask-servers/kasa-flask-server/readme.md
Reason: Keyword match (score: 1.50)

### flask-servers/kasa-flask-server/tests/test_time_of_use_electricity_pricing.py
Reason: Keyword match (score: 0.50)
Important symbols:
- TestGetCurrentPrice L360-574 - class TestGetCurrentPrice
- TestPricingStructure L37-119 - class TestPricingStructure
- TestWeekdayDetection L311-357 - class TestWeekdayDetection
- TestWinterDateRange L122-308 - class TestWinterDateRange
- make_toronto_datetime L32-34 - def make_toronto_datetime

## Suggested files to read before editing

1. argononerpi4case/case-fan-install.md
2. flask-servers/kasa-flask-server/docker-app/config.py
3. flask-servers/kasa-flask-server/docker-app/flask-app.py
4. flask-servers/kasa-flask-server/docker-app/my_logger.py
5. flask-servers/kasa-flask-server/docker-app/pyproject.toml
6. flask-servers/kasa-flask-server/docker-app/tester.py
7. flask-servers/kasa-flask-server/docker-app/time_of_use_electricity_pricing.py
8. flask-servers/kasa-flask-server/kube-configs/config_map.yml
9. flask-servers/kasa-flask-server/kube-configs/deployment.yml
10. flask-servers/kasa-flask-server/readme.md

## Confidence

HIGH

## Strict mode warnings

- No dependency paths found.
- No reverse dependency check performed.
- No test candidates found. Consider adding tests.


