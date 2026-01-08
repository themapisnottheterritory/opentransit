# AVL (Automatic Vehicle Location)

This module handles GPS data ingestion from vehicle modems and provides real-time fleet tracking.

## Overview

The AVL server listens for UDP packets from Pepwave routers (or compatible GPS modems) and stores location data in PostgreSQL.

## Architecture

```
[Pepwave BR1] --UDP:8080--> [AVL Server] --> [PostgreSQL]
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              busavl.log   busavl.last_location
                                    │             │
                                    │             └── Real-time tracking
                                    └── Historical data / NTD reporting
```

## Configuration

### Pepwave Router Setup

1. Enable GPS on the Pepwave device
2. Configure Location Report:
   - Protocol: UDP
   - Server: Your server IP
   - Port: 8080 (or as configured)
   - Format: Pepwave standard

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `UDP_PORT` | 8080 | Port to listen for GPS packets |

## Database Schema

```sql
-- Real-time location (one row per vehicle, updated constantly)
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

```bash
# Standalone
python -m avl.server

# With Docker
docker-compose up avl
```

## Testing

```bash
# Send test GPS packet
python -m avl.test_client --lat 28.8053 --lon -96.9853 --vehicle BUS001
```
