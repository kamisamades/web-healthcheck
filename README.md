# Web Healthcheck

CLI tool to monitor web services health (HTTP status, response time) with JSON config and rich console output.

## Features

- Check multiple HTTP/HTTPS endpoints from a JSON configuration file
- Measure response times and compare HTTP status codes
- Colorful, structured console report (OK / WARN / DOWN)
- Exit codes suitable for CI/CD pipelines (0 = all OK, 1 = at least one DOWN)
- Easy to extend: webhooks, dashboards, notifications

## Requirements

- Python 3.10+
- `pip`

## Installation

Clone the repository:

```bash
git clone https://github.com/kamisamades/web-healthcheck.git
cd web-healthcheck
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Create a `config.json` file (see [Configuration](#configuration)):

```json
{
  "services": [
    {
      "name": "Example",
      "url": "https://example.com",
      "timeout": 5,
      "expected_status": 200,
      "warn_threshold_ms": 500
    }
  ]
}
```

2. Run the healthcheck:

```bash
python healthcheck.py
```

Example output:

```text
Service         Status   Time     Message
Example         OK       210 ms   
API             DOWN     -        Expected 200, got 503
```

Exit codes:

- `0` → all services are OK
- `1` → at least one service is DOWN

## Configuration

The tool reads a `config.json` file in the current directory (or a custom path via `--config`).

### Example `config.json`

```json
{
  "services": [
    {
      "name": "Homepage",
      "url": "https://example.com",
      "timeout": 5,
      "expected_status": 200,
      "warn_threshold_ms": 500
    },
    {
      "name": "API Health",
      "url": "https://api.example.com/health",
      "timeout": 3,
      "expected_status": 200,
      "warn_threshold_ms": 300
    }
  ]
}
```

### Service fields

| Field              | Type    | Required | Default | Description |
|--------------------|---------|----------|---------|-------------|
| `name`             | string  | yes      | -       | Friendly name for the service |
| `url`              | string  | yes      | -       | Full HTTP/HTTPS URL to check |
| `timeout`          | number  | no       | `5`     | Request timeout in seconds |
| `expected_status`  | number  | no       | `200`   | Expected HTTP status code |
| `warn_threshold_ms`| number  | no       | `1000`  | Response time (ms) above which status becomes WARN |

### Status logic

- **OK**: HTTP status matches `expected_status` and response time ≤ `warn_threshold_ms`
- **WARN**: HTTP status matches but response time > `warn_threshold_ms`
- **DOWN**: HTTP status mismatch, timeout, or network error

## CLI options

```bash
python healthcheck.py --help
```

Available options:

- `--config PATH` → custom config file path (default: `config.json`)
- `--format json` → output results as JSON instead of rich table

## Project structure

```text
web-healthcheck/
├─ healthcheck.py       # Main CLI script
├─ config.json          # Example configuration
├─ requirements.txt     # Python dependencies
├─ README.md            # This file
└─ LICENSE              # MIT License
```

## Development

### Local testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python healthcheck.py
```

### Running with custom config

```bash
python healthcheck.py --config path/to/custom-config.json
```

## Changelog

### v1.1.0 (2026-09-25)

- Add option `--format` (table / json) : output results as rich table / JSON

### v1.0.0 (2026-09-25)

- Initial release
- JSON configuration support
- HTTP/HTTPS health checks with timeout
- Rich console output (OK / WARN / DOWN)
- Exit codes for CI/CD integration

## License

MIT License – see [LICENSE](LICENSE) file for details.

## Author

Author: [Maurice LECON](https://github.com/kamisamades). 
Web : [lebrun.dev](lebrun.dev)