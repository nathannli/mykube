#!/bin/bash
OUT=/var/lib/node_exporter/textfile_collector/highflow.prom
DATA=$(sensors -j 2>/dev/null | jq '.["highflownext-hid-3-1"]')

if [ -z "$DATA" ] || [ "$DATA" = "null" ]; then
  echo "[$(date)] ERROR: Failed to retrieve sensor data"
  exit 1
fi

# Extract + calculate
FLOW=$(echo $DATA | jq '."Flow [dL/h]".fan1_input / 10')
WATER_QUALITY=$(echo $DATA | jq '."Water quality [%]".fan2_input / 100')
CONDUCTIVITY=$(echo $DATA | jq '."Conductivity [nS/cm]".fan3_input')
COOLANT_TEMP=$(echo $DATA | jq '."Coolant temp".temp1_input')
DISSIPATED_POWER=$(echo $DATA | jq '."Dissipated power".power1_input / 1000')

cat <<EOF >$OUT
# HELP highflow_flow_lph Flow rate in liters per hour
# TYPE highflow_flow_lph gauge
highflow_flow_lph $FLOW
# HELP highflow_water_quality_percent Water quality percentage
# TYPE highflow_water_quality_percent gauge
highflow_water_quality_percent $WATER_QUALITY
# HELP highflow_conductivity_nscm Conductivity in nS/cm
# TYPE highflow_conductivity_nscm gauge
highflow_conductivity_nscm $CONDUCTIVITY
# HELP highflow_coolant_temp_celsius Coolant temperature in Celsius
# TYPE highflow_coolant_temp_celsius gauge
highflow_coolant_temp_celsius $COOLANT_TEMP
# HELP highflow_dissipated_power_watts Dissipated power in Watts
# TYPE highflow_dissipated_power_watts gauge
highflow_dissipated_power_watts $DISSIPATED_POWER
EOF

if [ $? -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] OK: Metrics written to $OUT"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to write metrics to $OUT"
  exit 1
fi