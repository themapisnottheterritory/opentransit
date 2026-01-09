"""
Bus Tracker API - REST endpoints for vehicle locations.

Provides JSON API for map frontends to display real-time vehicle positions.

Based on production code from Golden Crescent Regional Planning Commission.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from flask import Flask, jsonify, render_template, Response
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://opentransit:opentransit@localhost:5432/opentransit'
)


def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_bus_locations(max_age_minutes: int = 5) -> List[Dict[str, Any]]:
    """
    Get current bus locations from database.
    
    Args:
        max_age_minutes: Only return vehicles updated within this many minutes
        
    Returns:
        List of vehicle location dictionaries
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                vehicle_id as bus_id,
                latitude,
                longitude,
                speed,
                heading,
                timestamp as date,
                updated_at
            FROM busavl.last_location
            WHERE updated_at > NOW() - INTERVAL '%s minutes'
            ORDER BY vehicle_id
        """, (max_age_minutes,))
        
        locations = cursor.fetchall()
        
        # Convert to serializable format
        result = []
        for loc in locations:
            result.append({
                'bus_id': loc['bus_id'],
                'latitude': float(loc['latitude']) if loc['latitude'] else None,
                'longitude': float(loc['longitude']) if loc['longitude'] else None,
                'speed': float(loc['speed']) if loc['speed'] else 0,
                'heading': float(loc['heading']) if loc['heading'] else 0,
                'date': loc['date'].isoformat() if loc['date'] else None,
                'updated_at': loc['updated_at'].isoformat() if loc['updated_at'] else None
            })
        
        return result
        
    finally:
        cursor.close()
        conn.close()


def get_vehicle_history(vehicle_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get historical positions for a vehicle.
    
    Args:
        vehicle_id: Vehicle identifier
        hours: How many hours of history to retrieve
        
    Returns:
        List of position records
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                latitude,
                longitude,
                speed,
                heading,
                timestamp,
                created_at
            FROM busavl.log
            WHERE vehicle_id = %s
              AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 1000
        """, (vehicle_id, hours))
        
        records = cursor.fetchall()
        
        result = []
        for rec in records:
            result.append({
                'latitude': float(rec['latitude']) if rec['latitude'] else None,
                'longitude': float(rec['longitude']) if rec['longitude'] else None,
                'speed': float(rec['speed']) if rec['speed'] else 0,
                'heading': float(rec['heading']) if rec['heading'] else 0,
                'timestamp': rec['timestamp'].isoformat() if rec['timestamp'] else None
            })
        
        return result
        
    finally:
        cursor.close()
        conn.close()


# =============================================================================
# Routes
# =============================================================================

@app.route('/')
def index():
    """Serve the main map page."""
    return render_template('index.html')


@app.route('/bus_locations')
def bus_locations():
    """
    Get all current bus locations.
    
    Returns JSON array of vehicle positions.
    """
    try:
        locations = get_bus_locations()
        return jsonify(locations)
    except Exception as e:
        logger.error(f"Error fetching bus locations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vehicles')
def api_vehicles():
    """
    API endpoint for vehicle locations (alias for bus_locations).
    
    Query params:
        max_age: Maximum age in minutes (default: 5)
    """
    from flask import request
    max_age = request.args.get('max_age', 5, type=int)
    
    try:
        locations = get_bus_locations(max_age_minutes=max_age)
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(locations),
            'vehicles': locations
        })
    except Exception as e:
        logger.error(f"Error fetching vehicles: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vehicles/<vehicle_id>')
def api_vehicle_detail(vehicle_id: str):
    """
    Get details and recent history for a specific vehicle.
    
    Query params:
        hours: Hours of history to include (default: 24)
    """
    from flask import request
    hours = request.args.get('hours', 24, type=int)
    
    try:
        # Get current location
        locations = get_bus_locations(max_age_minutes=60)
        current = next((v for v in locations if v['bus_id'] == vehicle_id), None)
        
        # Get history
        history = get_vehicle_history(vehicle_id, hours=hours)
        
        return jsonify({
            'vehicle_id': vehicle_id,
            'current': current,
            'history': history,
            'history_count': len(history)
        })
    except Exception as e:
        logger.error(f"Error fetching vehicle {vehicle_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    host = os.environ.get('TRACKER_HOST', '0.0.0.0')
    port = int(os.environ.get('TRACKER_PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Bus Tracker API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
