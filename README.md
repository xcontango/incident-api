## Overview
Sample Django-DRF+Docker wepapp, wired together with a docker-compose file.
Meant to enable one to quickly spin up a local dev environment that requires the aforementioned software stack.

It illustrates the use of Django Rest Framework serving a json API which in turn utilizes a REST service
as a data source, and asynchronous sourcing of multiple urls via `aiohttp`.

## Setup

#### Prerequisites

This has only been tested on Ubuntu 20.04.

1. Docker and docker-compose

2. There are several settings that require confidential information not included with the repo.
See `.env.sample`.

#### Step-by-step

1. Clone the repo.

2. `cd incident-api`

3. You need an `.env` file: `cp .env.sample .env`.
Edit `.env` and change anything that conflicts with your local system.
You need credential and url settings.

4. Build the containers:

- `docker-compose build app`

5. Django setup:

- Django demands work. Run these commands:

- `docker-compose run --rm app migrate`

- `docker-compose run --rm app createsuperuser`. Follow the instructions.

6. If you got this far, run the app:

- `docker-compose up --build app`

- Navigate to `http://localhost:9000/api/v1/incidents` (if you didn't change the HOST_APP_PORT setting in `.env`).
