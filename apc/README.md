# APC (Automatic Passenger Counting)

Computer vision-based passenger counting using YOLOv8.

## Overview

This module uses machine learning to count passengers boarding and alighting buses via onboard cameras.

## Status

🔴 **Early Development** - Model training in progress

## Architecture

```
[IP Camera] --RTSP--> [APC Service] --counts--> [PostgreSQL]
                           │
                     [YOLOv8 Model]
```

## Hardware Requirements

- IP camera with RTSP stream per vehicle
- GPU recommended for inference (CPU possible but slower)
- Camera positioned to view door area

## Model Training

The model is being trained on annotated frames from actual bus cameras. Current training dataset: ~175 frames.

### Annotation Guidelines

When annotating training data:
- Use label: "Rider" (not "Person")
- Annotate all visible passengers
- Include partially visible passengers at frame edges

## Planned Features

- [ ] YOLOv8 inference pipeline
- [ ] RTSP stream ingestion
- [ ] Boarding/alighting detection via door zones
- [ ] Integration with AVL for location-tagged counts
- [ ] NTD reporting export

## Usage (Planned)

```bash
# Run APC service
python -m apc.service --camera rtsp://192.168.1.100/stream

# With Docker (GPU)
docker-compose --profile gpu up apc
```
