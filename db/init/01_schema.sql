-- OpenTransit Database Schema
-- Run this to initialize the database

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create schema for AVL data
CREATE SCHEMA IF NOT EXISTS busavl;

-- Real-time location (one row per vehicle, updated constantly)
CREATE TABLE IF NOT EXISTS busavl.last_location (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    timestamp TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historical log (append-only for NTD reporting)
CREATE TABLE IF NOT EXISTS busavl.log (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    timestamp TIMESTAMPTZ,
    raw_packet BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying historical data by vehicle and time
CREATE INDEX IF NOT EXISTS idx_busavl_log_vehicle_time 
    ON busavl.log (vehicle_id, created_at DESC);

-- Index for time-based queries (NTD reporting)
CREATE INDEX IF NOT EXISTS idx_busavl_log_created 
    ON busavl.log (created_at DESC);

-- Create schema for APC (Automatic Passenger Counting)
CREATE SCHEMA IF NOT EXISTS apc;

-- Passenger count events
CREATE TABLE IF NOT EXISTS apc.counts (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    boardings INTEGER DEFAULT 0,
    alightings INTEGER DEFAULT 0,
    load INTEGER DEFAULT 0,  -- Current passenger load
    door_id INTEGER DEFAULT 1,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    stop_id VARCHAR(50),  -- If matched to a GTFS stop
    confidence DECIMAL(3, 2),  -- ML model confidence
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vehicle queries
CREATE INDEX IF NOT EXISTS idx_apc_counts_vehicle_time 
    ON apc.counts (vehicle_id, timestamp DESC);

-- Create schema for GTFS data
CREATE SCHEMA IF NOT EXISTS gtfs;

-- Placeholder for GTFS static data (routes, stops, etc.)
-- These will be populated by gtfs_tools

-- Grant permissions
GRANT ALL ON SCHEMA busavl TO opentransit;
GRANT ALL ON SCHEMA apc TO opentransit;
GRANT ALL ON SCHEMA gtfs TO opentransit;
GRANT ALL ON ALL TABLES IN SCHEMA busavl TO opentransit;
GRANT ALL ON ALL TABLES IN SCHEMA apc TO opentransit;
GRANT ALL ON ALL TABLES IN SCHEMA gtfs TO opentransit;
GRANT ALL ON ALL SEQUENCES IN SCHEMA busavl TO opentransit;
GRANT ALL ON ALL SEQUENCES IN SCHEMA apc TO opentransit;
GRANT ALL ON ALL SEQUENCES IN SCHEMA gtfs TO opentransit;

-- Success message
DO $$ BEGIN RAISE NOTICE 'OpenTransit database initialized successfully'; END $$;
