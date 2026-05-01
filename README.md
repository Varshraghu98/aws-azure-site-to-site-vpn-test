# Cloud Image Upload Benchmark Project

This repository contains a Flask-based image upload/download application backed by MySQL, and a Python load script used to collect application-level performance metrics (latency and throughput) for single-cloud and cross-cloud (VPN) deployment comparisons.

## Project Purpose

The implementation supports the methodology described in your report section on data collection and performance metrics:

- Application-level metrics: upload/download latency and throughput.
- Cycle-based request simulation: one upload followed by one download.
- Standard duration runs: 120 seconds.
- Extended stability runs (cross-cloud VPN): 600 seconds.
- Optional network-level measurements outside this script: `ping` (latency) and `iperf` (bandwidth).

## Files and What They Do

- `main.py`
- Flask application exposing APIs for upload and download.
- Uses a storage abstraction (`ObjectStorage`) with a MySQL implementation (`MYSQLStorage`).
- Stores image binary data (`BLOB`) and metadata (`filename`, `content_type`) in MySQL.
- Endpoints:
  - `POST /upload`: upload image, returns `image_id`.
  - `GET /images/<image_id>`: returns image inline.

- `loadTest.py`
- Request simulation and benchmark collection script.
- Repeatedly executes cycles for a fixed test duration:
  - Upload image (`POST /upload`)
  - Download same image (`GET /images/<image_id>`)
- Tracks benchmark variables used in methodology:
  - `cycle_attempts`
  - `successful_cycles`
  - `upload_failures`
  - `download_failures`
- Collects latency lists for successful upload/download requests.
- Calculates and prints:
  - Mean latency
  - Standard deviation
  - P95
  - P99
  - Throughput (`Total Requests / Test Duration`)

- `test.jpg`
- Fixed input image used by `loadTest.py` for consistent and comparable runs across all deployment models.

## Runtime Requirements

- Python 3.x
- MySQL database
- Python packages:
  - `flask`
  - `pymysql`
  - `requests`

Install packages (example):

```bash
pip install flask pymysql requests
```

## Environment Variables

`main.py` reads the following environment variables:

- `STORAGE_PROVIDER` (must be `mysql`)
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `MYSQL_PORT` (optional, defaults to `3306`)

Example:

```bash
export STORAGE_PROVIDER=mysql
export MYSQL_HOST=127.0.0.1
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=cloud_images
export MYSQL_PORT=3306
```

## Database Table

Create the `images` table before running the app:

```sql
CREATE TABLE IF NOT EXISTS images (
  id VARCHAR(64) PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(255),
  data LONGBLOB NOT NULL
);
```

## How to Run

1. Start Flask application:

```bash
python main.py
```

2. Run benchmark script in another terminal:

```bash
python loadTest.py
```

## Methodology Mapping (Report Alignment)

This repository aligns with your report methodology as follows:

- Request simulation is executed from the same VM/instance as the Flask app to reduce client-side network variation.
- One cycle = one upload + one download.
- Latency metrics are calculated from successful requests.
- Throughput is calculated as total requests divided by configured test duration.
- Typical run duration is 120s, with extended 600s runs for cross-cloud VPN stability checks.

## Notes and Scope

- `loadTest.py` currently defaults to `TEST_DURATION = 600` seconds. Set to `120` for standard runs.
- Network-level metrics (`ping`, `iperf`) are part of the broader methodology but are run as separate tools/scripts, not inside `loadTest.py`.
- Current storage implementation supports MySQL only.
