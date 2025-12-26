#! /bin/bash
echo "Today is $(date '+%Y-%m-%d %H:%M:%S')"
echo $(nslookup ${DUCKDNS_DOMAIN}.duckdns.org)
previous_ip_address=$(nslookup ${DUCKDNS_DOMAIN}.duckdns.org | grep "Non-authoritative answer:" -A 2 | tail -n 1 | awk '{print $2}')
cur_ip_address=$(curl -s https://api.ipify.org)

if [ "$cur_ip_address" != "$previous_ip_address" ]; then
  echo "IP changed to $cur_ip_address, updating DuckDNS..."
  echo "Response: "
  RESPONSE=$(echo url="https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=" | curl -k -o ${DUCKDNS_LOG_FILE} -K -)
  echo "Previous IP: $previous_ip_address"
  echo "Current IP: $cur_ip_address"
else
  echo "IP is the same, no update needed"
fi

# Truncate log file to keep only the latest 10000 lines
if [ -f ${DUCKDNS_LOG_FILE} ]; then
  tail -n 10000 ${DUCKDNS_LOG_FILE} >${DUCKDNS_LOG_FILE}.tmp && mv ${DUCKDNS_LOG_FILE}.tmp ${DUCKDNS_LOG_FILE}
fi