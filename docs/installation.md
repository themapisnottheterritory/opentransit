# Installation Guide

## Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Python 3.11+ for local development

## Quick Install with Docker

```bash
# Clone the repository
git clone https://github.com/themapisnottheterritory/opentransit.git
cd opentransit

# Copy and edit environment file
cp .env.example .env
nano .env  # Edit with your settings

# Start the stack
docker-compose up -d

# Check status
docker-compose ps
```

## Manual Installation

### 1. Install PostgreSQL with PostGIS

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib postgis

# Create database
sudo -u postgres createdb opentransit
sudo -u postgres psql -d opentransit -c "CREATE EXTENSION postgis;"
```

### 2. Initialize Schema

```bash
psql -d opentransit -f db/init/01_schema.sql
```

### 3. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/opentransit"
export AVL_UDP_PORT=8080
export GTFS_RT_PORT=8081
```

### 5. Start Services

```bash
# Terminal 1: AVL Server
python -m avl.server

# Terminal 2: GTFS-RT Server
python -m gtfs_rt.server
```

## Vehicle Hardware Setup

See [AVL Setup](avl-setup.md) for configuring Pepwave routers and other GPS hardware.

## Verification

1. Send a test GPS packet:
   ```bash
   echo "BUS001,28.8053,-96.9853,25.5,180.0" | nc -u localhost 8080
   ```

2. Check GTFS-RT feed:
   ```bash
   curl http://localhost:8081/gtfs-rt/vehicle-positions.json
   ```

## Next Steps

- [Configure your vehicles](avl-setup.md)
- [Set up GTFS-RT consumers](gtfs-rt.md)
- [Create GTFS-Flex feeds](gtfs-flex.md)
