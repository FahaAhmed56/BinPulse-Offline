# ♻ BinPulse — Offline Smart Waste Bin Monitoring

A zero-dependency Python + SQLite + browser dashboard that simulates ultrasonic-bin sensors and models an offline-first waste-collection workflow. Designed for learning and GitHub portfolio demonstrations.

## Features

- Track five example bins in Lahore (illustrative locations)
- Simulate sensor readings for every bin and save them locally
- Manual readings with input validation
- Convert ultrasonic distance to estimated fill percentage (`fill% = (1 − measured_distance / bin_depth) × 100`)
- Collection thresholds: **normal <75%**, **collect 75–89%**, **critical ≥90%**
- Persist full reading history in SQLite, including unsynced telemetry
- Demonstrate local queue acknowledgement (not actual cloud synchronization)
- Responsive, accessible browser dashboard and JSON HTTP endpoints
- Python `unittest` suite and GitHub Actions CI

> This is a software simulation, not a tested physical IoT system. Without a real sensor, the values are synthetic or user-entered. Bin positions are illustrative, and the example queue acknowledgement does not transmit data over the internet.

## Quick start (Windows / Linux / macOS)

Requires **Python 3.10+**; no package installation necessary.

```bash
python -m binpulse.server
```

Open <http://127.0.0.1:8080> in a browser. The SQLite database is automatically created at `data/binpulse.sqlite3`.

To choose a custom port and DB location:

```bash
python -m binpulse.server --port 8090 --db mydata/bins.sqlite3
```

## Demo

1. Click **Simulate sensor readings** multiple times to grow the estimated waste levels.
2. Watch which bins cross the **collect** or **critical** thresholds.
3. Add a manual reading (e.g. 96% for BIN-101).
4. Observe the unsynced queue count.
5. Click **Acknowledge local queue** to mark records locally acknowledged; this is NOT cloud synchronization.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/bins` | Latest telemetry and collection status |
| GET | `/api/pending` | Unacknowledged readings |
| POST | `/api/readings` | Submit `{"bin_id":"BIN-101","fill_pct":82,"battery_pct":90}` |
| POST | `/api/simulate` | Generate one reading per bin |
| POST | `/api/sync` | Mark queue locally acknowledged (demo only) |

Example with curl:

```bash
curl -X POST http://127.0.0.1:8080/api/readings -H "Content-Type: application/json" -d '{"bin_id":"BIN-101","fill_pct":91}'
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Architecture

```text
Browser dashboard (HTML/CSS/JS)
          | HTTP JSON
Python ThreadingHTTPServer
          |
BinPulse core (validation, thresholds, simulation)
          |
SQLite (bins + timestamped readings + local sync flags)
```

### Hardware extension roadmap

Add an ESP32 with an ultrasonic sensor (or protected industrial distance sensor), proper ingress protection and weatherproof mounting. The ESP32 can save events locally while offline and transfer them over Wi-Fi, LoRa or a gateway when a link becomes available. A real sync service must use authenticated transport, durable acknowledgments and replay-safe event IDs. Waste moisture, unusual shapes, missing lids, vibration and battery life require physical calibration.

### Security notes

The demo binds to `127.0.0.1` by default and has no authentication. **Do not expose it publicly** or deploy directly to municipal infrastructure. Add authentication, authorization, rate limiting, HTTPS and backups for production use.

## License

MIT (see `LICENSE`).
