# logdog
Log indexing and search utilities. Licenced under MIT Licence

## Features

The module aim to be able to index and search logs at production scale.

Several utilities are bundled:

- A Dockerfile and compose to provide and initialize basic test local infrastructure (rabbittmq, timescaledb)
  and lauch the app without any install (other than docker)
- A rust project with two binaries
  - a light agent that watches a file and send every line to rabbitmq
  - an ingest json logs utility which inserts to timescaledb at amazing speeds (measured 10k logs per second)
- The python web app, which provides a get endpoint to search through logs

Used together, they can make a small DIY solution to gather logs from several sources and providing fast search through it, 
with enough performance to handle over a million log a day on a reasonably small virtual host.

## Contributing

Request features or fixes through this github issues.