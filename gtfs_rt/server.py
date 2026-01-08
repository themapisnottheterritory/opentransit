"""
GTFS-Realtime Server - HTTP server providing vehicle positions feed.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime

from aiohttp import web
import asyncpg
from google.transit import gtfs_realtime_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GTFSRealtimeServer:
    """Server that generates GTFS-Realtime feeds from AVL data."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self._feed_cache = None
        self._cache_time = 0
        self._cache_ttl = 15  # seconds
    
    async def get_vehicle_positions(self) -> gtfs_realtime_pb2.FeedMessage:
        """Generate GTFS-RT VehiclePositions feed."""
        now = time.time()
        
        # Return cached feed if still fresh
        if self._feed_cache and (now - self._cache_time) < self._cache_ttl:
            return self._feed_cache
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
        feed.header.timestamp = int(now)
        
        async with self.db_pool.acquire() as conn:
            # Get recent positions (within last 5 minutes)
            rows = await conn.fetch("""
                SELECT vehicle_id, latitude, longitude, speed, heading, timestamp
                FROM busavl.last_location
                WHERE updated_at > NOW() - INTERVAL '5 minutes'
            """)
            
            for row in rows:
                entity = feed.entity.add()
                entity.id = row['vehicle_id']
                
                vehicle = entity.vehicle
                vehicle.vehicle.id = row['vehicle_id']
                vehicle.vehicle.label = row['vehicle_id']
                
                vehicle.position.latitude = float(row['latitude'])
                vehicle.position.longitude = float(row['longitude'])
                
                if row['speed']:
                    vehicle.position.speed = float(row['speed'])
                if row['heading']:
                    vehicle.position.bearing = float(row['heading'])
                
                if row['timestamp']:
                    vehicle.timestamp = int(row['timestamp'].timestamp())
        
        self._feed_cache = feed
        self._cache_time = now
        
        logger.info(f"Generated feed with {len(feed.entity)} vehicles")
        return feed
    
    def feed_to_json(self, feed: gtfs_realtime_pb2.FeedMessage) -> dict:
        """Convert GTFS-RT feed to JSON for debugging."""
        return {
            "header": {
                "gtfsRealtimeVersion": feed.header.gtfs_realtime_version,
                "timestamp": feed.header.timestamp
            },
            "entity": [
                {
                    "id": e.id,
                    "vehicle": {
                        "vehicleId": e.vehicle.vehicle.id,
                        "position": {
                            "latitude": e.vehicle.position.latitude,
                            "longitude": e.vehicle.position.longitude,
                            "speed": e.vehicle.position.speed,
                            "bearing": e.vehicle.position.bearing
                        },
                        "timestamp": e.vehicle.timestamp
                    }
                }
                for e in feed.entity
            ]
        }


async def handle_vehicle_positions(request):
    """Handle /gtfs-rt/vehicle-positions endpoint (protobuf)."""
    server = request.app['gtfs_server']
    feed = await server.get_vehicle_positions()
    return web.Response(
        body=feed.SerializeToString(),
        content_type='application/x-protobuf'
    )


async def handle_vehicle_positions_json(request):
    """Handle /gtfs-rt/vehicle-positions.json endpoint (JSON debug)."""
    server = request.app['gtfs_server']
    feed = await server.get_vehicle_positions()
    return web.json_response(server.feed_to_json(feed))


async def handle_health(request):
    """Health check endpoint."""
    return web.json_response({"status": "ok", "timestamp": int(time.time())})


async def init_app() -> web.Application:
    """Initialize the web application."""
    database_url = os.environ.get('DATABASE_URL', 'postgresql://opentransit:opentransit@localhost:5432/opentransit')
    
    logger.info("Connecting to database...")
    db_pool = await asyncpg.create_pool(database_url)
    
    app = web.Application()
    app['db_pool'] = db_pool
    app['gtfs_server'] = GTFSRealtimeServer(db_pool)
    
    app.router.add_get('/gtfs-rt/vehicle-positions', handle_vehicle_positions)
    app.router.add_get('/gtfs-rt/vehicle-positions.json', handle_vehicle_positions_json)
    app.router.add_get('/health', handle_health)
    
    return app


def main():
    """Start the GTFS-RT server."""
    port = int(os.environ.get('GTFS_RT_PORT', '8081'))
    logger.info(f"Starting GTFS-RT server on port {port}")
    web.run_app(init_app(), port=port)


if __name__ == '__main__':
    main()
