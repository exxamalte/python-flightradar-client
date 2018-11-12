# python-flightradar24-client

[![Build Status](https://travis-ci.org/exxamalte/python-flightradar24-client.svg)](https://travis-ci.org/exxamalte/python-flightradar24-client)
[![Coverage Status](https://coveralls.io/repos/github/exxamalte/python-flightradar24-client/badge.svg?branch=master)](https://coveralls.io/github/exxamalte/python-flightradar24-client?branch=master)

This library provides convenient access to a local [Flightradar24](https://www.flightradar24.com/) feed.


## Installation
`pip install flightradar24-client`

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

### Flightradar24 Feed

The Flightradar24 Feed mode uses the JSON data made available by the `fr24feed`
service (normally under `http://localhost:8754/flights.json`).

`Flightradar24FlightsFeed` and `Flightradar24FlightsFeedAggregator` support
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
from flightradar24_client.fr24_flights import Flightradar24FlightsFeed
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed = Flightradar24FlightsFeed((-33.5, 151.5))
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed.update())
```

#### Feed Aggregator

```python
import asyncio
from flightradar24_client.fr24_flights import Flightradar24FlightsFeedAggregator
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed_aggregator = Flightradar24FlightsFeedAggregator((-33.5, 151.5))
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
from flightradar24_client.dump1090_aircrafts import Dump1090AircraftsFeed
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed = Dump1090AircraftsFeed((-33.5, 151.5))
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed.update())
```

#### Feed Aggregator

```python
import asyncio
from flightradar24_client.dump1090_aircrafts import Dump1090AircraftsFeedAggregator
# Home Coordinates: Latitude: -33.5, Longitude: 151.5
feed_aggregator = Dump1090AircraftsFeedAggregator((-33.5, 151.5))
LOOP = asyncio.get_event_loop()
status, entries = LOOP.run_until_complete(feed_aggregator.update())
```
