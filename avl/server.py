"""
AVL Server - UDP listener for GPS data from Pepwave routers.

Receives NMEA GPRMC sentences, validates checksums, parses coordinates,
and stores in PostgreSQL.

Based on production code from Golden Crescent Regional Planning Commission.
"""

import asyncio
import logging
import math
import os
import operator
from datetime import datetime
from functools import reduce
from typing import Optional, Tuple, Dict, Any

import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# NMEA Parsing (from original busavl.py)
# =============================================================================

def nmea_checksum(sentence: str) -> Tuple[str, int, int]:
    """
    Validate NMEA sentence checksum.
    
    The checksum is calculated by XORing all characters between '$' and '*'.
    
    Args:
        sentence: Raw NMEA sentence string
        
    Returns:
        Tuple of (data portion, received checksum, calculated checksum)
        
    Raises:
        ValueError: If sentence is malformed or checksum doesn't match
    """
    sentence = sentence.strip("\r\n")
    
    if '*' not in sentence:
        raise ValueError("Invalid NMEA sentence, missing '*'")
    
    nmeadata, checksum = sentence.split('*', 1)
    
    # XOR all characters between '$' and '*'
    calculated_checksum = reduce(operator.xor, (ord(char) for char in nmeadata[1:]), 0)
    
    try:
        received = int(checksum, 16)
        if received == calculated_checksum:
            return nmeadata, received, calculated_checksum
        else:
            raise ValueError(
                f"Checksum mismatch. Calculated: {calculated_checksum:02X}, "
                f"Received: {checksum}"
            )
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Checksum '{checksum}' is not valid hex")
        raise


def nmea_to_decimal(nmea_coord: float) -> float:
    """
    Convert NMEA coordinate (DDMM.MMMM) to decimal degrees.
    
    NMEA format: DDMM.MMMM where DD = degrees, MM.MMMM = minutes
    
    Args:
        nmea_coord: Coordinate in NMEA format (e.g., 2848.3180 for 28°48.318')
        
    Returns:
        Decimal degrees (e.g., 28.805300)
    """
    degrees = int(nmea_coord / 100)
    minutes = nmea_coord - (degrees * 100)
    decimal = degrees + (minutes / 60)
    return round(decimal, 7)


class GPRMCData:
    """Parsed GPRMC sentence data."""
    
    def __init__(
        self,
        unit_id: str,
        latitude: float,
        longitude: float,
        speed_mph: float,
        heading: float,
        timestamp: datetime,
        status: str,
        raw: str
    ):
        self.unit_id = unit_id
        self.latitude = latitude
        self.longitude = longitude
        self.speed_mph = speed_mph
        self.heading = heading
        self.timestamp = timestamp
        self.status = status  # 'A' = active/valid, 'V' = void/invalid
        self.raw = raw
    
    def __repr__(self):
        return (
            f"<GPRMC {self.unit_id} ({self.latitude:.6f}, {self.longitude:.6f}) "
            f"{self.speed_mph:.1f}mph hdg={self.heading}>"
        )


def parse_gprmc(sentence: str) -> Optional[GPRMCData]:
    """
    Parse a GPRMC NMEA sentence.
    
    GPRMC format:
    $GPRMC,HHMMSS.SS,A,DDMM.MMMM,N,DDDMM.MMMM,W,speed,heading,DDMMYY,,,mode*checksum
    
    Pepwave adds unit ID in field 13.
    
    Args:
        sentence: Raw NMEA sentence
        
    Returns:
        GPRMCData object or None if parsing fails
    """
    try:
        fields = sentence.split(',')
        
        # Must be GPRMC with enough fields
        if fields[0] != '$GPRMC' or len(fields) < 10:
            return None
        
        # Check for valid fix (field 2 = 'A' for active)
        status = fields[2]
        
        # Must have latitude data
        if not fields[3]:
            return None
        
        # Parse coordinates
        lat_nmea = float(fields[3])
        lat_dir = fields[4]  # N or S
        lon_nmea = float(fields[5])
        lon_dir = fields[6]  # E or W
        
        latitude = nmea_to_decimal(lat_nmea)
        longitude = nmea_to_decimal(lon_nmea)
        
        # Apply direction
        if lat_dir == 'S':
            latitude = -latitude
        if lon_dir == 'W':
            longitude = -longitude
        
        # Speed: knots to mph (1 knot = 1.150779 mph)
        speed_knots = float(fields[7]) if fields[7] else 0.0
        speed_mph = round(speed_knots * 1.150779, 2)
        
        # Heading
        heading = float(fields[8]) if fields[8] else 0.0
        
        # Timestamp: combine date (DDMMYY) and time (HHMMSS.SS)
        time_str = fields[1]
        date_str = fields[9]
        timestamp = datetime.strptime(date_str + time_str, '%d%m%y%H%M%S.%f')
        
        # Unit ID: Pepwave puts this in field 13 (first 4 chars)
        unit_id = 'UNKNOWN'
        if len(fields) > 13 and fields[13]:
            # Extract unit ID, removing checksum if present
            unit_field = fields[13].split('*')[0]
            unit_id = unit_field[:4] if len(unit_field) >= 4 else unit_field
        
        return GPRMCData(
            unit_id=unit_id,
            latitude=latitude,
            longitude=longitude,
            speed_mph=speed_mph,
            heading=heading,
            timestamp=timestamp,
            status=status,
            raw=sentence
        )
        
    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse GPRMC: {e}")
        return None


# =============================================================================
# Database Operations
# =============================================================================

class AVLDatabase:
    """Async PostgreSQL database handler for AVL data."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Establish connection pool."""
        logger.info("Connecting to PostgreSQL...")
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        logger.info("Database connection pool established")
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")
    
    async def store_location(self, data: GPRMCData) -> bool:
        """
        Store GPS data in both last_location and log tables.
        
        Args:
            data: Parsed GPRMC data
            
        Returns:
            True if successful
        """
        if not self.pool:
            logger.error("Database not connected")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Upsert to last_location (current position)
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
                    """, data.unit_id, data.latitude, data.longitude,
                        data.speed_mph, data.heading, data.timestamp)
                    
                    # Append to log (historical record)
                    await conn.execute("""
                        INSERT INTO busavl.log 
                            (vehicle_id, latitude, longitude, speed, heading, timestamp, raw_packet)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, data.unit_id, data.latitude, data.longitude,
                        data.speed_mph, data.heading, data.timestamp, 
                        data.raw.encode('utf-8'))
            
            logger.info(f"Stored: {data}")
            return True
            
        except asyncpg.PostgresError as e:
            logger.error(f"Database error storing location: {e}")
            return False


# =============================================================================
# UDP Server
# =============================================================================

class AVLProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for NMEA data from Pepwave routers."""
    
    def __init__(self, database: AVLDatabase):
        self.database = database
        self.transport = None
    
    def connection_made(self, transport):
        self.transport = transport
        logger.info("AVL UDP server ready")
    
    def datagram_received(self, data: bytes, addr: tuple):
        """Handle incoming UDP packet containing NMEA sentences."""
        try:
            # Decode packet
            payload = data.decode('utf-8', errors='ignore').strip()
            
            # Process each line (packet may contain multiple sentences)
            for line in payload.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Validate checksum
                    nmea_checksum(line)
                    
                    # Parse GPRMC
                    gps_data = parse_gprmc(line)
                    
                    if gps_data:
                        # Store asynchronously
                        asyncio.create_task(self.database.store_location(gps_data))
                    else:
                        logger.debug(f"Non-GPRMC or invalid sentence from {addr}")
                        
                except ValueError as e:
                    logger.warning(f"NMEA error from {addr}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing packet from {addr}: {e}")
    
    def error_received(self, exc):
        logger.error(f"UDP error: {exc}")


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Start the AVL server."""
    # Configuration from environment
    database_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://opentransit:opentransit@localhost:5432/opentransit'
    )
    udp_host = os.environ.get('AVL_HOST', '0.0.0.0')
    udp_port = int(os.environ.get('AVL_UDP_PORT', '8080'))
    
    # Initialize database
    database = AVLDatabase(database_url)
    await database.connect()
    
    # Start UDP server
    logger.info(f"Starting AVL server on {udp_host}:{udp_port}")
    loop = asyncio.get_event_loop()
    
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: AVLProtocol(database),
        local_addr=(udp_host, udp_port)
    )
    
    logger.info(f"Listening for NMEA data on UDP {udp_host}:{udp_port}")
    
    try:
        # Run forever
        await asyncio.sleep(float('inf'))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        transport.close()
        await database.close()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    asyncio.run(main())
