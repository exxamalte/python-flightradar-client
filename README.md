# python-flightradar24-client

[![Build Status](https://travis-ci.org/exxamalte/python-flightradar24-client.svg)](https://travis-ci.org/exxamalte/python-flightradar24-client)
[![Coverage Status](https://coveralls.io/repos/github/exxamalte/python-flightradar24-client/badge.svg?branch=master)](https://coveralls.io/github/exxamalte/python-flightradar24-client?branch=master)

This library provides convenient access to a local [Flightradar24](https://www.flightradar24.com/) feed.


## Installation
`pip install flightradar24-client`

## Usage

### Flightradar24 Feed

The Flightradar24 Feed mode uses the JSON data made available by the `fr24feed`
service (normally under `http://localhost:8754/flights.json`).

```python
from flightradar24_client.fr24_flights import Flightradar24FlightsFeed
feed = Flightradar24FlightsFeed((-33.5, 151.5))
status, entries = feed.update()
```

### Dump1090 Feed

The Dump1090 Feed mode uses the JSON data made available by the `dump1090-mutability` 
service (normally under `http://localhost:8888/data/aircraft.json`).

```python
from flightradar24_client.dump1090_aircrafts import Dump1090AircraftsFeed
feed = Dump1090AircraftsFeed((-33.5, 151.5))
status, entries = feed.update()
```
