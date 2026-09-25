import json
import time
import argparse
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

console = Console()

VERSION = "1.1"

import json
from datetime import datetime, timezone

def print_json_report(all_results: list, filtered_results: list) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ok_count = sum(1 for r in all_results if r["status"] == "OK")
    warn_count = sum(1 for r in all_results if r["status"] == "WARN")
    down_count = sum(1 for r in all_results if r["status"] == "DOWN")

    report = {
        "timestamp": now,
        "services": filtered_results,
        "summary": {
            "total": len(all_results),
            "ok": ok_count,
            "warn": warn_count,
            "down": down_count,
        },
    }

    print(json.dumps(report, indent=2))

def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise SystemExit(1)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def check_service(service: dict) -> dict:
    name = service["name"]
    url = service["url"]
    timeout = service.get("timeout", 5)
    expected = service.get("expected_status", 200)
    warn_threshold_ms = service.get("warn_threshold_ms", 1000)

    try:
        start = time.perf_counter()
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = time.perf_counter() - start

        status_code = resp.status_code
        elapsed_ms = int(elapsed * 1000)

        if status_code != expected:
            status = "DOWN"
            message = f"Expected {expected}, got {status_code}"
        elif elapsed_ms > warn_threshold_ms:
            status = "WARN"
            message = f"Slow response: {elapsed_ms} ms"
        else:
            status = "OK"
            message = ""

        return {
            "name": name,
            "status": status,
            "http_status": status_code,
            "time_ms": elapsed_ms,
            "message": message,
        }

    except requests.RequestException as e:
        elapsed = time.perf_counter() - start
        return {
            "name": name,
            "status": "DOWN",
            "http_status": None,
            "time_ms": int(elapsed * 1000),
            "message": str(e),
        }

def print_report(results: list) -> None:
    table = Table(title=f"Web Healthcheck Results (v{VERSION})")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Time", justify="right")
    table.add_column("Message", style="yellow")

    for r in results:
        time_str = f"{r['time_ms']} ms" if r['time_ms'] is not None else "-"
        status_style = {
            "OK": "green",
            "WARN": "yellow",
            "DOWN": "red",
        }.get(r["status"], "white")

        table.add_row(
            r["name"],
            f"[{status_style}]{r['status']}[/{status_style}]",
            time_str,
            r["message"],
        )

    console.print(table)

def main():
    parser = argparse.ArgumentParser(
        description="Check HTTP services health"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table (default) or json",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show WARN and DOWN services",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    services = config.get("services", [])

    if not services:
        console.print("[yellow]No services defined in config[/yellow]")
        raise SystemExit(0)

    results = [check_service(s) for s in services]
    filtered_results = results
    if args.quiet:
        filtered_results = [
            r for r in results if r["status"] in ("WARN", "DOWN")
        ]

    if args.format == "json":
        print_json_report(results, filtered_results)

    else:
        print_report(results)

    any_down = any(r["status"] == "DOWN" for r in results)
    raise SystemExit(1 if any_down else 0)

if __name__ == "__main__":
    main()