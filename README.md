# Mawaqit Api

This repo extends the original api with support for ARM cpus and adds extra features like searching using Searxng

Mawaqi Api is a Rest Api for [mawaqit.net](https://mawaqit.net) using FastApi framework,
the mawaqit.net website gives you the prayer times for more than 8000 mosques around the world,
the idea behind this api is to create an api web app that uses the mawaqit website as data source
to fetch prayer times and return them in json with the minimum information needed,
the current website is using php so it's returning the whole html every get request.

## Documentation

Find the installation and usage documentation [here](https://mrsofiane.me/mawaqit-api).

## Tests

Install dependencies with `python -m pip install -r requirements.txt`, then run
`python -m pytest`. The default suite uses isolated unit and API integration tests
without calling external services.

To also verify the API against real data from the public Mawaqit website, run:

```sh
RUN_LIVE_TESTS=1 python -m pytest -m live
```

The live smoke test bypasses the scraper's Redis cache and checks that the prayer
times endpoint returns all six valid times. It makes a real HTTPS request with a
20-second timeout and can fail if Mawaqit is unavailable or changes its page format.
It is skipped by default to keep CI independent of upstream availability.

## License

[MIT](https://github.com/mrsofiane/mawaqit-api/blob/main/LICENSE.md)
