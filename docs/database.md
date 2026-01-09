# Database

OpenTransit uses **PostgreSQL** with **PostGIS** as its primary database.

## Why PostgreSQL?

| Feature | Benefit for Transit |
|---------|---------------------|
| **PostGIS extension** | Industry-standard geospatial support. Enables efficient geofencing, route matching, "vehicles within polygon" queries, and distance calculations. |
| **GTFS ecosystem compatibility** | Most GTFS tools (gtfsdb, OpenTripPlanner, Transitland) expect PostgreSQL. |
| **JSON/JSONB support** | Flexible storage for varying vehicle telemetry formats without schema changes. |
| **Mature & reliable** | Battle-tested in production transit systems worldwide. |
| **Fully open source** | No licensing concerns or Oracle ownership issues. |

## For MySQL Users

We understand many small agencies already run MySQL and may be hesitant to add another database. Our approach:

1. **Schema design** — We avoid PostgreSQL-specific syntax where possible, making future MySQL support easier.

2. **Docker deployment** — The recommended Docker setup handles PostgreSQL automatically. You don't need to be a PostgreSQL expert.

3. **Future MySQL adapter** — We plan to add MySQL/MariaDB support for agencies that require it. The core application logic is database-agnostic where feasible.

If you're currently running AVL data in MySQL and want to migrate, see [MySQL Migration Guide](mysql-migration.md).

## Schema Overview

OpenTransit uses three schemas:

```
opentransit (database)
├── busavl          # Vehicle location data
│   ├── last_location   # Current position per vehicle (upsert)
│   └── log             # Historical positions (append-only)
│
├── apc             # Automatic Passenger Counting
│   └── counts          # Boarding/alighting events
│
└── gtfs            # GTFS static data (optional)
    ├── stops
    ├── routes
    └── ...
```

## PostGIS Usage

PostGIS is used for:

- **Geofencing** — Trigger announcements when vehicles enter stop zones
- **Service area queries** — "Is this pickup location within our service area?"
- **Distance calculations** — NTD reporting, route deviation detection
- **Spatial indexing** — Fast queries on large historical datasets

Example query (find vehicles within 100m of a stop):
```sql
SELECT vehicle_id, latitude, longitude
FROM busavl.last_location
WHERE ST_DWithin(
    ST_MakePoint(longitude, latitude)::geography,
    ST_MakePoint(-96.9853, 28.8053)::geography,
    100  -- meters
);
```

## MySQL Compatibility Notes

For contributors working on MySQL support, these PostgreSQL features need alternatives:

| PostgreSQL | MySQL Equivalent |
|------------|------------------|
| `SERIAL` | `AUTO_INCREMENT` |
| `TIMESTAMPTZ` | `TIMESTAMP` (with timezone handling in app) |
| `DECIMAL(10,7)` | Same ✓ |
| `BYTEA` | `BLOB` |
| `ON CONFLICT DO UPDATE` | `INSERT ... ON DUPLICATE KEY UPDATE` |
| PostGIS `ST_*` functions | MySQL 8.0 spatial functions (limited) |

The main challenge is PostGIS — MySQL 8.0 has spatial support but it's less mature. Agencies using MySQL may have reduced geospatial functionality.

## Connection Configuration

Set the database connection via environment variable:

```bash
# PostgreSQL (default)
DATABASE_URL=postgresql://user:password@localhost:5432/opentransit

# Future MySQL support
# DATABASE_URL=mysql://user:password@localhost:3306/opentransit
```

## Backup & Maintenance

```bash
# Backup (PostgreSQL)
pg_dump -Fc opentransit > opentransit_backup.dump

# Restore
pg_restore -d opentransit opentransit_backup.dump

# Vacuum (run periodically for performance)
vacuumdb --analyze opentransit
```

For Docker deployments, see [Operations Guide](operations.md).
