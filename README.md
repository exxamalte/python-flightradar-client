# python-flightradar24-client

This library provides convenient access to a local [Flightradar24](https://www.flightradar24.com/) feed.


## Installation
`pip install flightradar24-client`

## Usage

```python
from flightradar24_client.fr24_flights import Flightradar24FlightsFeed
feed = Flightradar24FlightsFeed((-33.5, 151.5))
status, entries = feed.update()
```
