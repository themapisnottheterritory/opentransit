# AVL (Automatic Vehicle Location)

This module handles GPS data ingestion from Pepwave routers and provides real-time fleet tracking.

## Overview

The AVL system consists of two components:

1. **server.py** - UDP listener that receives NMEA sentences from vehicles
2. **tracker.py** - Flask web app providing REST API and map interface

```
[Pepwave BR1] --UDP:8080--> [AVL Server] --> [PostgreSQL]
                                                  │
                                    ┌─────────────┴─────────────┐
                                    │                           │
                              busavl.log              busavl.last_location
                              (historical)               (real-time)
                                    │                           │
                                    │                           ▼
                                    │                    [Tracker API]
                                    │                           │
                                    ▼                           ▼
                              NTD Reporting              Map Interface
```

## Hardware Support

### Pepwave MAX BR1 Series

The server is designed for Pepwave routers that output NMEA GPRMC sentences via UDP.

**Router Configuration:**
1. Enable GPS in the router admin panel
2. Configure Location Report:
   - Protocol: **UDP**
   - Server: Your server IP
   - Port: **8080** (or as configured)
   - Format: NMEA

### NMEA GPRMC Format

The server parses standard NMEA GPRMC sentences:

```
$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,270.0,080125,,,A,1234*5A
       │         │ │         │ │          │ │    │     │       │    └─ Unit ID
       │         │ │         │ │          │ │    │     │       └─ Mode
       │         │ │         │ │          │ │    │     └─ Date (DDMMYY)
       │         │ │         │ │          │ │    └─ Heading
       │         │ │         │ │          │ └─ Speed (knots)
       │         │ │         │ │          └─ E/W
       │         │ │         │ └─ Longitude (DDDMM.MMMM)
       │         │ │         └─ N/S
       │         │ └─ Latitude (DDMM.MMMM)
       │         └─ Status (A=active, V=void)
       └─ Time (HHMMSS.SS) UTC
```

**Pepwave-specific:** The unit ID is extracted from field 13 (first 4 characters).

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://opentransit:opentransit@localhost:5432/opentransit` | PostgreSQL connection string |
| `AVL_UDP_PORT` | `8080` | UDP port for NMEA data |
| `AVL_HOST` | `0.0.0.0` | Listen address |
| `TRACKER_PORT` | `5000` | HTTP port for tracker API |

## Database Schema

```sql
-- Real-time location (one row per vehicle)
CREATE TABLE busavl.last_location (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    timestamp TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historical log (append-only)
CREATE TABLE busavl.log (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    timestamp TIMESTAMPTZ,
    raw_packet BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Usage

### Start AVL Server (UDP Listener)

```bash
# Direct
python -m avl.server

# With Docker
docker-compose up avl
```

### Start Tracker API (Web Interface)

```bash
# Direct
python -m avl.tracker

# With Docker
docker-compose up tracker
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Map interface |
| `/bus_locations` | GET | All current vehicle positions (JSON) |
| `/api/vehicles` | GET | Vehicle positions with metadata |
| `/api/vehicles/<id>` | GET | Single vehicle with history |
| `/health` | GET | Health check |

### Example API Response

```json
{
  "timestamp": "2025-01-08T12:30:00",
  "count": 5,
  "vehicles": [
    {
      "bus_id": "1234",
      "latitude": 28.80530,
      "longitude": -96.98533,
      "speed": 25.5,
      "heading": 180.0,
      "date": "2025-01-08T12:29:55",
      "updated_at": "2025-01-08T12:29:55"
    }
  ]
}
```

## Testing

### Send Test GPS Packet

```bash
# Simple test (CSV format - for basic testing)
echo "BUS01,28.8053,-96.9853,25.5,180.0" | nc -u localhost 8080

# NMEA format (production format)
echo '$GPRMC,143025.00,A,2848.3180,N,09659.1200,W,21.5,270.0,080125,,,A,1234*XX' | nc -u localhost 8080
```

### Run Unit Tests

```bash
pytest tests/test_avl.py -v
```

## Migrating from MySQL

If you're running the original `busavl.py` with MySQL/MariaDB:

1. Export your data:
```bash
mysql -u user -p busavl -e "SELECT * FROM avllog" > avllog.csv
mysql -u user -p busavl -e "SELECT * FROM last_location" > last_location.csv
```

2. Import to PostgreSQL:
```bash
psql -d opentransit -c "\copy busavl.log FROM 'avllog.csv' CSV HEADER"
psql -d opentransit -c "\copy busavl.last_location FROM 'last_location.csv' CSV HEADER"
```

See [MySQL Migration Guide](../docs/mysql-migration.md) for details.

## Credits

Based on production code from [Golden Crescent Regional Planning Commission](https://www.gcrpc.org), Victoria, TX.
