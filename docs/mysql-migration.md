# MySQL Migration Guide

For agencies migrating existing AVL data from MySQL to OpenTransit's PostgreSQL.

## Overview

If you're currently running vehicle tracking in MySQL (like GCRPC was), this guide will help you migrate your historical data to OpenTransit.

## Prerequisites

- Access to your existing MySQL database
- OpenTransit PostgreSQL instance running
- `mysql` and `psql` command-line tools

## Schema Mapping

| MySQL Table/Column | OpenTransit Equivalent |
|--------------------|------------------------|
| `your_location_table` | `busavl.last_location` |
| `your_history_table` | `busavl.log` |
| `vehicle_id` | `vehicle_id` (VARCHAR) |
| `lat` / `latitude` | `latitude` (DECIMAL 10,7) |
| `lng` / `longitude` | `longitude` (DECIMAL 10,7) |
| `timestamp` | `timestamp` (TIMESTAMPTZ) |
| `created_at` | `created_at` (TIMESTAMPTZ) |

## Migration Steps

### 1. Export from MySQL

```bash
# Export current locations
mysql -u user -p your_database -e "
SELECT vehicle_id, latitude, longitude, speed, heading, timestamp 
FROM your_location_table" > locations.csv

# Export historical data (may be large)
mysql -u user -p your_database -e "
SELECT vehicle_id, latitude, longitude, speed, heading, timestamp, created_at
FROM your_history_table
WHERE created_at > '2024-01-01'" > history.csv
```

### 2. Import to PostgreSQL

```bash
# Import current locations
psql -d opentransit -c "\copy busavl.last_location(vehicle_id, latitude, longitude, speed, heading, timestamp) FROM 'locations.csv' WITH CSV HEADER"

# Import historical data
psql -d opentransit -c "\copy busavl.log(vehicle_id, latitude, longitude, speed, heading, timestamp, created_at) FROM 'history.csv' WITH CSV HEADER"
```

### 3. Verify

```bash
psql -d opentransit -c "SELECT COUNT(*) FROM busavl.last_location"
psql -d opentransit -c "SELECT COUNT(*) FROM busavl.log"
```

## Handling Differences

### Timestamps

MySQL `DATETIME` doesn't store timezone info. If your data is in local time (e.g., America/Chicago):

```sql
-- After import, convert to timestamptz
UPDATE busavl.log 
SET timestamp = timestamp AT TIME ZONE 'America/Chicago';
```

### Vehicle IDs

If your MySQL uses integer IDs and you want to keep them:
- They'll be stored as strings in OpenTransit
- `123` becomes `'123'`

## Cutover Strategy

1. **Parallel run** — Run both systems simultaneously for a week
2. **Verify data** — Compare counts and spot-check locations
3. **Switch UDP endpoint** — Point Pepwave routers to OpenTransit server
4. **Monitor** — Watch for any missed packets
5. **Decommission** — Turn off old MySQL ingestion

## Need Help?

Open an issue: https://github.com/themapisnottheterritory/opentransit/issues
