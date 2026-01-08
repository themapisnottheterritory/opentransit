"""
AVL Server - UDP listener for GPS data from vehicle modems.

Supports Pepwave MAX BR1 format by default.
"""

import asyncio
import logging
import os
import struct
from datetime import datetime
from typing import Optional

# Database
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPSPacket:
    """Parsed GPS packet from vehicle modem."""
    
    def __init__(
        self,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        speed: float,
        heading: float,
        timestamp: datetime,
        raw: bytes
    ):
        self.vehicle_id = vehicle_id
        self.latitude = latitude
        self.longitude = longitude
        self.speed = speed
        self.heading = heading
        self.timestamp = timestamp
        self.raw = raw
    
    def __repr__(self):
        return f"<GPSPacket {self.vehicle_id} ({self.latitude}, {self.longitude})>"


class PepwaveDecoder:
    """Decode GPS packets from Pepwave routers."""
    
    @staticmethod
    def decode(data: bytes) -> Optional[GPSPacket]:
        """
        Decode a Pepwave GPS packet.
        
        TODO: Implement actual Pepwave packet format.
        This is a placeholder that assumes a simple CSV format for testing.
        """
        try:
            # Placeholder: assumes "vehicle_id,lat,lon,speed,heading,timestamp"
            text = data.decode('utf-8').strip()
            parts = text.split(',')
            
            if len(parts) >= 5:
                return GPSPacket(
                    vehicle_id=parts[0],
                    latitude=float(parts[1]),
                    longitude=float(parts[2]),
                    speed=float(parts[3]) if len(parts) > 3 else 0.0,
                    heading=float(parts[4]) if len(parts) > 4 else 0.0,
                    timestamp=datetime.utcnow(),
                    raw=data
                )
        except Exception as e:
            logger.warning(f"Failed to decode packet: {e}")
        
        return None


class AVLProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for AVL data."""
    
    def __init__(self, db_pool: asyncpg.Pool, decoder=None):
        self.db_pool = db_pool
        self.decoder = decoder or PepwaveDecoder()
    
    def connection_made(self, transport):
        self.transport = transport
        logger.info("AVL UDP server ready")
    
    def datagram_received(self, data: bytes, addr: tuple):
        """Handle incoming GPS packet."""
        logger.debug(f"Received {len(data)} bytes from {addr}")
        
        packet = self.decoder.decode(data)
        if packet:
            asyncio.create_task(self.store_location(packet))
    
    async def store_location(self, packet: GPSPacket):
        """Store GPS data in database."""
        async with self.db_pool.acquire() as conn:
            # Update last_location (upsert)
            await conn.execute("""
                INSERT INTO busavl.last_location 
                    (vehicle_id, latitude, longitude, speed, heading, timestamp, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (vehicle_id) DO UPDATE SET
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    speed = EXCLUDED.speed,
                    heading = EXCLUDED.heading,
                    timestamp = EXCLUDED.timestamp,
                    updated_at = NOW()
            """, packet.vehicle_id, packet.latitude, packet.longitude,
                packet.speed, packet.heading, packet.timestamp)
            
            # Append to log
            await conn.execute("""
                INSERT INTO busavl.log 
                    (vehicle_id, latitude, longitude, speed, heading, timestamp, raw_packet)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, packet.vehicle_id, packet.latitude, packet.longitude,
                packet.speed, packet.heading, packet.timestamp, packet.raw)
            
            logger.info(f"Stored location for {packet.vehicle_id}: ({packet.latitude}, {packet.longitude})")


async def main():
    """Start the AVL server."""
    database_url = os.environ.get('DATABASE_URL', 'postgresql://opentransit:opentransit@localhost:5432/opentransit')
    udp_port = int(os.environ.get('UDP_PORT', '8080'))
    
    logger.info(f"Connecting to database...")
    db_pool = await asyncpg.create_pool(database_url)
    
    logger.info(f"Starting AVL server on UDP port {udp_port}")
    loop = asyncio.get_event_loop()
    
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: AVLProtocol(db_pool),
        local_addr=('0.0.0.0', udp_port)
    )
    
    try:
        await asyncio.sleep(float('inf'))  # Run forever
    finally:
        transport.close()
        await db_pool.close()


if __name__ == '__main__':
    asyncio.run(main())
