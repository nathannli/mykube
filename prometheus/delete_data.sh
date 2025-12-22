curl -X POST "http://localhost:31090/api/v1/admin/tsdb/delete_series" \
  --data-urlencode 'match[]={__name__="electricity_price"}' \
  --data-urlencode 'start=2025-12-22T19:00:00Z' \
  --data-urlencode 'end=2025-12-22T21:00:00Z'


curl -X POST "http://localhost:31090/api/v1/admin/tsdb/clean_tombstones"