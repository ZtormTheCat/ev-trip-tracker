# EV Trip Tracker

A Home Assistant custom integration that automatically tracks and logs EV trips with detailed metrics.
This is mainly made for EV integrations that don't deliver all the calculated and estimated infos like consumption and avg. speed themselves (In my case Volkswagen group).

## Requirements
These entities are needed for the integration to fully function
- Engine/Car state, to track when car is driving
- Odometer
- Battery in percent
- Location

## Features

- **Automatic trip detection** - Starts/stops tracking based on driving state sensor
- **Configurable trip end delay** - Prevents false trip endings from brief stops
- **Configurable minimum trip distance and duration**
- **Trip metrics:**
  - Distance (km)
  - Energy used (kWh)
  - Duration
  - Average speed (km/h)
  - Start/end battery percentage
  - Start/end elevation (via Open-Meteo API)
  - Elevation difference
  - Start/end/average temperature (via Open-Meteo API)
- **Events** - Fires `ev_trip_tracker_trip_completed` event for automations

## Installation

### HACS (Custom Repository)

1. Open HACS → 3-dot menu → Custom repositories
2. Add `https://github.com/ZtormTheCat/ev_trip_tracker` as Integration
3. Search "EV Trip Tracker" → Download
4. Restart Home Assistant

### Manual

1. Copy `custom_components/ev_trip_tracker` to your `config/custom_components/` folder
2. Restart Home Assistant
#### Possible additions:
- Sample temperature during trip to get better average

## Open points/ideas
- Stop tracking when starting charging, to avoid negative consumption
- Track temperature and potentially weather/rainfall during the trip in fixed intervals
- Support other data formats, like consumption or battery in kwh
