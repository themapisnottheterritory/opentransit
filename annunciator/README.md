# Annunciator

Automated next-stop audio announcements.

## Overview

This module provides ADA-compliant automated stop announcements triggered by GPS geofences.

## Status

🔴 **Planned** - Not yet started

## Concept

```
[AVL Location] --> [Geofence Check] --> [TTS Engine] --> [Audio Output]
                         │
                   [GTFS Stops]
```

## Planned Features

- [ ] Geofence-based announcement triggering
- [ ] Text-to-speech integration (local or cloud)
- [ ] Pre-recorded audio support
- [ ] Multi-language support
- [ ] Integration with onboard audio system
- [ ] ADA compliance (timing, volume)

## Hardware Requirements

- Onboard computer with audio output
- Speaker system
- GPS feed from AVL module

## Configuration (Planned)

```yaml
announcements:
  trigger_distance_meters: 100  # Announce when this close to stop
  voice: en-US-Standard-C
  volume: 0.8
  pre_announcement: "Next stop:"
  
stops:
  - id: STOP001
    name: "Main Street Transit Center"
    custom_audio: /audio/main_street.mp3  # Optional
```
