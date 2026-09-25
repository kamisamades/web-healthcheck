import argparse
import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table


VERSION = "1.3"
DEFAULT_CONFIG = "config.json"

console = Console()
stop_requested = False


def load_config(config_path: str) -> dict:
    path = Path(config_path)

    if not path.exists():
        console.print(
            f"[red]Config file not found: {config_path}[/red]"
        )
        raise SystemExit(1)

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        console.print(
            f"[red]Invalid JSON configuration: {error}[/red]"
        )
        raise SystemExit(1)


def check_service(service: dict) -> dict:
    name = service["name"]
    url = service["url"]
    timeout = service.get("timeout", 5)
    expected_status = service.get("expected_status", 200)
    warn_threshold_ms = service.get(
        "warn_threshold_ms",
        1000,
    )

    start = time.perf_counter()

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
        )

        elapsed = time.perf_counter() - start
        elapsed_ms = int(elapsed * 1000)

        if response.status_code != expected_status:
            status = "DOWN"
            message = (
                f"Expected {expected_status}, "
                f"got {response.status_code}"
            )
        elif elapsed_ms > warn_threshold_ms:
            status = "WARN"
            message = f"Slow response: {elapsed_ms} ms"
        else:
            status = "OK"
            message = ""

        return {
            "name": name,
            "status": status,
            "http_status": response.status_code,
            "time_ms": elapsed_ms,
            "message": message,
        }

    except requests.RequestException as error:
        elapsed = time.perf_counter() - start
        elapsed_ms = int(elapsed * 1000)

        return {
            "name": name,
            "status": "DOWN",
            "http_status": None,
            "time_ms": elapsed_ms,
            "message": str(error),
        }


def print_report(results: list[dict], title: str) -> None:
    table = Table(
        title=f"{title} (v{VERSION})"
    )

    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("HTTP", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("Message", style="yellow")

    status_styles = {
        "OK": "green",
        "WARN": "yellow",
        "DOWN": "red",
    }

    for result in results:
        status = result["status"]
        status_style = status_styles.get(status, "white")

        http_status = (
            str(result["http_status"])
            if result["http_status"] is not None
            else "-"
        )

        time_ms = (
            f"{result['time_ms']} ms"
            if result["time_ms"] is not None
            else "-"
        )

        table.add_row(
            result["name"],
            f"[{status_style}]{status}[/{status_style}]",
            http_status,
            time_ms,
            result["message"],
        )

    console.print(table)


def build_json_report(
    all_results: list[dict],
    displayed_results: list[dict],
) -> dict:
    ok_count = sum(
        1
        for result in all_results
        if result["status"] == "OK"
    )

    warn_count = sum(
        1
        for result in all_results
        if result["status"] == "WARN"
    )

    down_count = sum(
        1
        for result in all_results
        if result["status"] == "DOWN"
    )

    return {
        "timestamp": datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "services": displayed_results,
        "summary": {
            "total": len(all_results),
            "ok": ok_count,
            "warn": warn_count,
            "down": down_count,
        },
    }


def print_json_report(
    all_results: list[dict],
    displayed_results: list[dict],
) -> None:
    report = build_json_report(
        all_results,
        displayed_results,
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
    )


def run_check_cycle(config: dict, args, cycle_number: int | None = None) -> bool:
    services = config.get("services", [])

    if not services:
        console.print(
            "[yellow]No services defined in config[/yellow]"
        )
        return False

    if cycle_number is None:
        title = "Web Healthcheck Results"
    else:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        title = (
            f"Check #{cycle_number} - {timestamp}"
        )

    results = [
        check_service(service)
        for service in services
    ]

    if args.quiet:
        displayed_results = [
            result
            for result in results
            if result["status"] in ("WARN", "DOWN")
        ]
    else:
        displayed_results = results

    if args.format == "json":
        print_json_report(
            results,
            displayed_results,
        )
    else:
        print_report(
            displayed_results,
            title,
        )

    return any(
        result["status"] == "DOWN"
        for result in results
    )


def handle_sigint(signum, frame):
    global stop_requested

    stop_requested = True
    console.print(
        "\n[yellow]Stopping healthcheck...[/yellow]"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check HTTP services health"
    )

    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=(
            "Path to config file "
            f"(default: {DEFAULT_CONFIG})"
        ),
    )

    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table or json",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show WARN and DOWN services",
    )

    parser.add_argument(
        "--watch",
        type=int,
        metavar="SECONDS",
        help="Run checks every N seconds",
    )

    return parser.parse_args()


def main() -> None:
    global stop_requested

    args = parse_arguments()

    if args.watch is not None and args.watch <= 0:
        console.print(
            "[red]Watch interval must be positive[/red]"
        )
        raise SystemExit(1)

    signal.signal(
        signal.SIGINT,
        handle_sigint,
    )

    config = load_config(args.config)

    if args.watch is None:
        has_down = run_check_cycle(
            config,
            args,
        )
        raise SystemExit(1 if has_down else 0)

    cycle_number = 0
    last_cycle_has_down = False

    while not stop_requested:
        cycle_number += 1

        last_cycle_has_down = run_check_cycle(
            config,
            args,
            cycle_number,
        )

        if stop_requested:
            break

        try:
            time.sleep(args.watch)

        except KeyboardInterrupt:
            stop_requested = True

    raise SystemExit(
        1 if last_cycle_has_down else 0
    )


if __name__ == "__main__":
    main()