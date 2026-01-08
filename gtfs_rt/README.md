# GTFS-Realtime Server

This module provides a GTFS-Realtime feed from live vehicle location data.

## Overview

The GTFS-RT server queries the AVL database and serves vehicle positions in the standard GTFS-Realtime protobuf format.

## Endpoints

| Endpoint | Format | Description |
|----------|--------|-------------|
| `/gtfs-rt/vehicle-positions` | Protobuf | Vehicle positions feed |
| `/gtfs-rt/vehicle-positions.json` | JSON | Vehicle positions (debug) |
| `/health` | JSON | Health check |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `GTFS_RT_PORT` | 8081 | HTTP server port |
| `REFRESH_INTERVAL` | 15 | Seconds between feed updates |

## Usage

```bash
# Standalone
python -m gtfs_rt.server

# With Docker
docker-compose up gtfs-rt
```

## Consuming the Feed

### Google Maps / Transit App

Provide the URL to your GTFS-RT feed:
```
https://your-server.com/gtfs-rt/vehicle-positions
```

### OpenTripPlanner

```json
{
  "feedId": "gcrpc",
  "gtfsRtUrl": "https://your-server.com/gtfs-rt/vehicle-positions"
}
```

### Python Example

```python
from google.transit import gtfs_realtime_pb2
import requests

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('http://localhost:8081/gtfs-rt/vehicle-positions')
feed.ParseFromString(response.content)

for entity in feed.entity:
    if entity.HasField('vehicle'):
        v = entity.vehicle
        print(f"Vehicle {v.vehicle.id}: ({v.position.latitude}, {v.position.longitude})")
```
