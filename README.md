# python-flightradar-client

[![Build Status](https://github.com/exxamalte/python-flightradar-client/workflows/CI/badge.svg?branch=master)](https://github.com/exxamalte/python-flightradar-client/actions?workflow=CI)
[![codecov](https://codecov.io/gh/exxamalte/python-flightradar-client/branch/master/graph/badge.svg?token=EPCZQ50XZX)](https://codecov.io/gh/exxamalte/python-flightradar-client)
[![PyPi](https://img.shields.io/pypi/v/flightradar-client.svg)](https://pypi.python.org/pypi/flightradar-client)
[![Version](https://img.shields.io/pypi/pyversions/flightradar-client.svg)](https://pypi.python.org/pypi/flightradar-client)

This library provides convenient access to a local [Flightradar24](https://www.flightradar24.com/) feed.


## Installation
`pip install flightradar-client`

## Usage

This library currently support two different flavour of flight data, 
provided by the `fr24feed` and `dump1090-mutability` services that are
automatically installed when building your own 
[Pi24 ADS-B receiver](https://www.flightradar24.com/build-your-own).

For each flavour the library provides two modes of access. The `*Feed` class
fetches data once when calling `update` and transforms it into `FeedEntry` 
objects. The `*FeedAggregator` class keeps a bit of history and with each 
subsequent `update` call it tries to fill in any gaps (coordinates and callsign 
at the moment) missing in the latest data set fetched.

### Flightradar Feed

The Flightradar Feed mode uses the JSON data made available by the `fr24feed`
service (normally under `http://localhost:8754/flights.json`).

`FlightradarFlightsFeed` and `FlightradarFlightsFeedAggregator` support
the same parameters:

| Name               | Type                                                                                                 | Description                                                                                   |
|--------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `home_coordinates` | required, tuple of latitude and longitude                                                            | Used to calculate the distance to each aircraft.                                              |
| `filter_radius`    | optional, float value in kilometres, default: don't filter by distance                               | Only aircrafts within this radius around the home coordinates are included in the result set. |
| `url`              | optional, full url to access the Pi24 ADS-B receiver JSON, default: construct with hostname and port | Define if you have customised access to Pi24 ADS-B receiver or use HTTPS for example.         |
| `hostname`         | optional, hostname of the Pi24 ADS-B receiver, default: `localhost`                                  | Define if you are not running this library on your Pi24 ADS-B receiver.                       |
| `port`             | optional, port of the Pi24 ADS-B receiver's flights service, default: `8754`                         | Define if you have configured a different port on your Pi24 ADS-B receiver.                   |

#### Feed

```python
import asyncio
import aiohttp
from flightradar_client.fr24feed_flights import FlightradarFlightsFeed
session = aiohttp.ClientSession()
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed = FlightradarFlightsFeed((-33.5, 151.5), session)
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed.update())
```

#### Feed Aggregator

```python
import asyncio
import aiohttp
from flightradar_client.fr24feed_flights import FlightradarFlightsFeedAggregator
session = aiohttp.ClientSession()
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed_aggregator = FlightradarFlightsFeedAggregator((-33.5, 151.5), session)
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed_aggregator.update())
```

### Dump1090 Feed

The Dump1090 Feed mode uses the JSON data made available by the `dump1090-mutability` 
service (normally under `http://localhost:8888/data/aircraft.json`).

`Dump1090AircraftsFeed` and `Dump1090AircraftsFeedAggregator` support
the same parameters:

| Name               | Type                                                                                                 | Description                                                                                   |
|--------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `home_coordinates` | required, tuple of latitude and longitude                                                            | Used to calculate the distance to each aircraft.                                              |
| `filter_radius`    | optional, float value in kilometres, default: don't filter by distance                               | Only aircrafts within this radius around the home coordinates are included in the result set. |
| `url`              | optional, full url to access the Pi24 ADS-B receiver JSON, default: construct with hostname and port | Define if you have customised access to Pi24 ADS-B receiver or use HTTPS for example.         |
| `hostname`         | optional, hostname of the Pi24 ADS-B receiver, default: `localhost`                                  | Define if you are not running this library on your Pi24 ADS-B receiver.                       |
| `port`             | optional, port of the Pi24 ADS-B receiver's dump1090 service, default: `8888`                        | Define if you have configured a different port on your Pi24 ADS-B receiver.                   |

#### Feed

```python
import asyncio
import aiohttp
from flightradar_client.dump1090_aircrafts import Dump1090AircraftsFeed
session = aiohttp.ClientSession()
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed = Dump1090AircraftsFeed((-33.5, 151.5), session)
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed.update())
```

#### Feed Aggregator

```python
import asyncio
import aiohttp
from flightradar_client.dump1090_aircrafts import Dump1090AircraftsFeedAggregator
session = aiohttp.ClientSession()
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed_aggregator = Dump1090AircraftsFeedAggregator((-33.5, 151.5), session)
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed_aggregator.update())
```
