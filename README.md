# OpenTransit

**A complete open-source software stack for small and rural transit agencies.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is OpenTransit?

OpenTransit is a modular, open-source transit technology stack designed to give small and rural transit agencies access to the same capabilities as large metro systems — without the $20k+/year vendor lock-in.

Built by [Golden Crescent Regional Planning Commission](https://www.gcrpc.org) (Victoria, TX) and released for the benefit of transit agencies everywhere.

## Components

| Component | Description | Status |
|-----------|-------------|--------|
| **avl** | Automatic Vehicle Location - GPS tracking and fleet management | 🟡 In Development |
| **gtfs-rt** | GTFS-Realtime feed server | 🟡 Alpha |
| **gtfs-tools** | Static GTFS and GTFS-Flex feed generators | 🟡 In Development |
| **apc** | Automatic Passenger Counting using computer vision | 🔴 Early Development |
| **annunciator** | Next-stop audio announcements | 🔴 Planned |
| **ntd-reporter** | Automated NTD (National Transit Database) reporting | 🔴 Planned |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VEHICLE                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Pepwave BR1 │  │   Camera    │  │   Speaker   │              │
│  │ (GPS/LTE)   │  │   (APC)     │  │(Annunciator)│              │
│  └──────┬──────┘  └──────┬──────┘  └──────▲──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │ UDP            │ RTSP           │ Audio
          ▼                ▼                │
┌─────────────────────────────────────────────────────────────────┐
│                        SERVER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  AVL Server │  │ APC Service │  │ Annunciator │              │
│  │  (Python)   │  │  (YOLO)     │  │  Service    │              │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘              │
│         │                │                                       │
│         ▼                ▼                                       │
│  ┌────────────────────────────────┐                             │
│  │         PostgreSQL             │                             │
│  │  - busavl.last_location        │                             │
│  │  - busavl.log                  │                             │
│  │  - apc.counts                  │                             │
│  └───────────────┬────────────────┘                             │
│                  │                                               │
│         ┌────────┴────────┐                                     │
│         ▼                 ▼                                     │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  GTFS-RT    │  │ NTD Reporter│                               │
│  │  Server     │  │             │                               │
│  └──────┬──────┘  └─────────────┘                               │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
    ┌───────────┐
    │ Transit   │
    │ Apps      │
    │ (Google,  │
    │  Transit) │
    └───────────┘
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/themapisnottheterritory/opentransit.git
cd opentransit

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start with Docker Compose
docker-compose up -d
```

## Hardware Requirements

### Minimum (AVL only)
- Any cellular modem with GPS (we use Pepwave MAX BR1 Mini)
- Server with 2GB RAM, 20GB storage

### Recommended (Full stack)
- Pepwave MAX BR1 Mini LTEA per vehicle
- IP camera per vehicle (for APC)
- Server with 8GB RAM, 100GB storage, GPU recommended for APC

## Documentation

- [Installation Guide](docs/installation.md)
- [AVL Setup](docs/avl-setup.md)
- [GTFS-RT Configuration](docs/gtfs-rt.md)
- [GTFS-Flex Feed Creation](docs/gtfs-flex.md)
- [Passenger Counting](docs/apc.md)
- [NTD Reporting](docs/ntd.md)

## Contributing

We welcome contributions! This project is built by transit people, for transit people.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Why Open Source?

Small transit agencies are often forced to choose between:
1. Expensive vendor solutions ($20k+/year)
2. No technology at all
3. Cobbling together unsupported tools

OpenTransit provides a fourth option: professional-grade transit technology that agencies can run themselves, modify to their needs, and share improvements with the community.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Golden Crescent Regional Planning Commission
- The transit technology community
- [MobilityData](https://mobilitydata.org/) for GTFS standards

---

**Built with ❤️ in Victoria, Texas**
