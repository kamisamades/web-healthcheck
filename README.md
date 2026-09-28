# Web Healthcheck

CLI tool to monitor web services health (HTTP status, response time) with JSON config and rich console output, plus domain investigation features (DNS, SPF, DMARC, WHOIS).

## Features

### Healthcheck

- Check multiple HTTP/HTTPS endpoints from a JSON configuration file
- Measure response times and compare HTTP status codes
- Colorful, structured console report (OK / WARN / DOWN)
- Exit codes suitable for CI/CD pipelines (0 = all OK, 1 = at least one DOWN)
- Watch mode: periodic checks every N seconds

### Domain information

- Resolve common DNS records: A, AAAA, NS, MX, TXT, SOA, CNAME
- Detect SPF and DMARC records for email authentication
- Retrieve WHOIS information: creation date, expiration date, registrar, name servers, status
- Output as rich table or JSON

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

### Healthcheck

1. Create a `config.json` file:

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

### Domain information

Query DNS and WHOIS information for a domain:

```bash
python domain_info.py example.com
```

Example output (table):

```text
Domain: example.com

DNS Records
-----------
A:      93.184.216.34
AAAA:   2606:2800:220:1:248:1893:25c8:1948
NS:     a.iana-servers.net
        b.iana-servers.net
MX:     10 mail.example.com
CNAME:  None
SOA:    Master: ns1.example.com
        Responsible: hostmaster.example.com
        Serial: 2024092801
TXT:    v=spf1 include:_spf.example.com ~all

Email Security
--------------
SPF:    v=spf1 include:_spf.example.com ~all
DMARC:  v=DMARC1; p=reject; rua=mailto:dmarc@example.com

WHOIS
-----
Created:    1995-08-14T04:00:00Z
Expires:    2028-08-13T04:00:00Z
Registrar:  Example Registrar, Inc.
Name servers: ['ns1.example.com', 'ns2.example.com']
Status:     ['clientDeleteProhibited', 'clientTransferProhibited']
```

JSON output:

```bash
python domain_info.py example.com --format json
```

## Configuration

### Healthcheck config

The tool reads a `config.json` file in the current directory (or a custom path via `--config`).

#### Example `config.json`

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

#### Service fields

| Field              | Type    | Required | Default | Description |
|--------------------|---------|----------|---------|-------------|
| `name`             | string  | yes      | -       | Friendly name for the service |
| `url`              | string  | yes      | -       | Full HTTP/HTTPS URL to check |
| `timeout`          | number  | no       | `5`     | Request timeout in seconds |
| `expected_status`  | number  | no       | `200`   | Expected HTTP status code |
| `warn_threshold_ms`| number  | no       | `1000`  | Response time (ms) above which status becomes WARN |

#### Status logic

- **OK**: HTTP status matches `expected_status` and response time ≤ `warn_threshold_ms`
- **WARN**: HTTP status matches but response time > `warn_threshold_ms`
- **DOWN**: HTTP status mismatch, timeout, or network error

## CLI options

### healthcheck.py

```bash
python healthcheck.py --help
```

Available options:

- `--config PATH` → custom config file path (default: `config.json`)
- `--format json` → output results as JSON instead of rich table
- `--quiet` → only show WARN and DOWN services
- `--watch N` → run checks every N seconds (watch mode)

### domain_info.py

```bash
python domain_info.py --help
```

Available options:

- `--format json` → output results as JSON instead of rich table

## Project structure

```text
web-healthcheck/
├─ healthcheck.py       # HTTP healthcheck CLI
├─ domain_info.py       # DNS and WHOIS domain info CLI
├─ config.json          # Example healthcheck configuration
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

# Healthcheck
python healthcheck.py

# Domain info
python domain_info.py example.com
```

### Running with custom config

```bash
python healthcheck.py --config path/to/custom-config.json
```

## Changelog

### v1.3.0 (2026-09-28)

- Add `domain_info.py` for DNS and WHOIS domain investigation
- Resolve common DNS records: A, AAAA, NS, MX, TXT, SOA, CNAME
- Detect SPF and DMARC records for email authentication
- Retrieve WHOIS information: creation date, expiration date, registrar, name servers, status
- Output as rich table or JSON

### v1.2.0 (2026-09-25)

- Add `--watch` mode for periodic checks
- Add `--format json` option
- Add `--quiet` option to filter OK services

### v1.1.0 (2026-09-25)

- Add `--format json` option
- Improve console output with Rich

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