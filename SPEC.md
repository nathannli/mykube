# Kasa TPAP support

## §G

Use personal `python-kasa` TPAP fork. Choose KP125M transport by configured IP.

## §C

- Docker image installs dependencies from `docker-app/requirements.txt`.
- Pin fork at commit `38a48ebeb25418b027b25251128c965d5f394063`.
- KLAP stays default for KP125M IPs.
- Only IPs in `TPAP_KP125M_IPS` use TPAP.
- No device-state change during metrics collection or connection tests.

## §I

- I1: `docker-app/requirements.txt` selects runtime `python-kasa` source.
- I2: `Config.TPAP_KP125M_IPS` lists TPAP KP125M IPs.
- I3: `connect_to_kp125m_device(ip)` selects connection parameters from `ip`.
- I4: `/metrics` and `/poweroff` retain current response and power-control behavior.

## §V

- V1: Runtime `python-kasa` install resolves fork commit `38a48ebeb25418b027b25251128c965d5f394063`.
- V2: `ip in TPAP_KP125M_IPS` selects `DeviceEncryptionType.Tpap`; every other KP125M IP selects `DeviceEncryptionType.Klap`.
- V3: All KP125M metrics, power-off, and power-state flows use `connect_to_kp125m_device(ip)` transport selection.
- V4: TPAP configuration does not alter HS300 behavior or Flask route contracts.

## §T

|id|status|task|cites|
|---|---|---|---|
|T1|x|Pin custom `python-kasa` fork in runtime requirements.|V1,I1|
|T2|x|Add TPAP KP125M IP config and connection-parameter selector.|V2,I2,I3|
|T3|x|Use selected KP125M parameters when connecting devices.|V2,V3,I3|
|T4|x|Add focused tests for KLAP default and TPAP override.|V2,V3,V4|

## §B

|id|date|cause|fix|
|---|---|---|---|
|B1|2026-08-10|Summer price tests stale versus configured rates.|Separate pricing-test update; no Kasa invariant.|
