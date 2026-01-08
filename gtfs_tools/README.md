# GTFS Tools

Tools for generating static GTFS and GTFS-Flex feeds.

## Overview

This module provides utilities for creating and managing:
- Standard GTFS feeds for fixed-route services
- GTFS-Flex feeds for demand-responsive/paratransit services
- Feed validation and testing

## Status

🔴 **In Development** - Coming soon

## Planned Features

- [ ] GTFS-Flex feed generator
- [ ] Command-line interface
- [ ] Service area polygon editor
- [ ] Booking rules configuration
- [ ] Feed validation
- [ ] Export to ZIP

## Usage (Planned)

```bash
# Generate GTFS-Flex feed
python -m gtfs_tools.flex_generator --config agency.yaml --output feed.zip

# Validate existing feed
python -m gtfs_tools.validator feed.zip
```
