import argparse
import json
from datetime import datetime
from typing import Any

import dns.resolver
import whois
from dns.exception import DNSException
from rich.console import Console
from rich.table import Table


console = Console()


def resolve_txt_records(domain: str) -> list[str]:
    """Return all TXT records for a domain."""
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        records = []

        for record in answers:
            value = "".join(
                part.decode("utf-8")
                if isinstance(part, bytes)
                else str(part)
                for part in record.strings
            )
            records.append(value)

        return records

    except DNSException:
        return []


def get_spf_record(domain: str) -> str | None:
    """Return the SPF TXT record of a domain."""
    for record in resolve_txt_records(domain):
        if record.lower().startswith("v=spf1"):
            return record

    return None


def get_dmarc_record(domain: str) -> str | None:
    """Return the DMARC TXT record of a domain."""
    dmarc_domain = f"_dmarc.{domain}"

    try:
        answers = dns.resolver.resolve(dmarc_domain, "TXT")
        records = []

        for record in answers:
            value = "".join(
                part.decode("utf-8")
                if isinstance(part, bytes)
                else str(part)
                for part in record.strings
            )
            records.append(value)

        for value in records:
            if value.lower().startswith("v=dmarc1"):
                return value

    except DNSException:
        return None

    return None


def resolve_common_records(domain: str) -> dict[str, Any]:
    """Resolve common DNS records."""
    result: dict[str, Any] = {
        "A": [],
        "AAAA": [],
        "NS": [],
        "MX": [],
        "TXT": [],
        "SOA": None,
        "CNAME": None,
    }

    try:
        answers = dns.resolver.resolve(domain, "A")
        result["A"] = [
            record.to_text()
            for record in answers
        ]
    except DNSException:
        pass

    try:
        answers = dns.resolver.resolve(domain, "AAAA")
        result["AAAA"] = [
            record.to_text()
            for record in answers
        ]
    except DNSException:
        pass

    try:
        answers = dns.resolver.resolve(domain, "NS")
        result["NS"] = [
            record.to_text()
            for record in answers
        ]
    except DNSException:
        pass

    try:
        answers = dns.resolver.resolve(domain, "MX")
        result["MX"] = [
            {
                "preference": record.preference,
                "exchange": record.exchange.to_text(),
            }
            for record in answers
        ]
    except DNSException:
        pass

    result["TXT"] = resolve_txt_records(domain)

    try:
        answers = dns.resolver.resolve(domain, "SOA")
        soa = answers[0]

        result["SOA"] = {
            "mname": soa.mname.to_text(),
            "rname": soa.rname.to_text(),
            "serial": soa.serial,
            "refresh": soa.refresh,
            "retry": soa.retry,
            "expire": soa.expire,
            "minimum": soa.minimum,
        }
    except DNSException:
        pass

    try:
        answers = dns.resolver.resolve(domain, "CNAME")
        result["CNAME"] = answers[0].to_text()
    except DNSException:
        pass

    return result


def normalize_whois_value(value: Any) -> Any:
    """Normalize WHOIS values for JSON output."""
    if isinstance(value, list):
        return [
            normalize_whois_value(item)
            for item in value
        ]

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def get_whois_info(domain: str) -> dict[str, Any]:
    """Return WHOIS information for a domain."""
    try:
        data = whois.whois(domain)

        return {
            "created": normalize_whois_value(
                data.creation_date
            ),
            "expires": normalize_whois_value(
                data.expiration_date
            ),
            "registrar": data.registrar,
            "name_servers": normalize_whois_value(
                data.name_servers
            ),
            "status": normalize_whois_value(
                data.status
            ),
        }

    except Exception as error:
        return {
            "error": str(error),
        }


def build_report(domain: str) -> dict[str, Any]:
    common_records = resolve_common_records(domain)

    return {
        "domain": domain,
        "dns": {
            "common_records": common_records,
            "spf": get_spf_record(domain),
            "dmarc": get_dmarc_record(domain),
        },
        "whois": get_whois_info(domain),
    }


def display_value(value: Any) -> str:
    """Convert a value into readable text for Rich."""
    if value is None:
        return "[yellow]None[/yellow]"

    if isinstance(value, list):
        if not value:
            return "[yellow]None[/yellow]"

        return "\n".join(
            str(item)
            for item in value
        )

    return str(value)


def print_table_report(report: dict[str, Any]) -> None:
    domain = report["domain"]
    dns_info = report["dns"]
    common = dns_info["common_records"]
    whois_info = report.get("whois", {})

    console.print(
        f"\n[cyan bold]Domain: {domain}[/cyan bold]\n"
    )

    dns_table = Table(
        title="DNS Records",
        show_header=False,
    )
    dns_table.add_column(
        "Type",
        style="magenta",
    )
    dns_table.add_column("Value")

    dns_table.add_row(
        "A:",
        display_value(common.get("A")),
    )

    dns_table.add_row(
        "AAAA:",
        display_value(common.get("AAAA")),
    )

    dns_table.add_row(
        "NS:",
        display_value(common.get("NS")),
    )

    mx_records = common.get("MX", [])

    if mx_records:
        mx_value = "\n".join(
            f"{record['preference']} "
            f"{record['exchange']}"
            for record in mx_records
        )
    else:
        mx_value = "[yellow]None[/yellow]"

    dns_table.add_row("MX:", mx_value)

    dns_table.add_row(
        "CNAME:",
        display_value(common.get("CNAME")),
    )

    soa = common.get("SOA")

    if soa:
        soa_value = (
            f"Master: {soa['mname']}\n"
            f"Responsible: {soa['rname']}\n"
            f"Serial: {soa['serial']}\n"
            f"Refresh: {soa['refresh']}\n"
            f"Retry: {soa['retry']}\n"
            f"Expire: {soa['expire']}\n"
            f"Minimum: {soa['minimum']}"
        )
    else:
        soa_value = "[yellow]None[/yellow]"

    dns_table.add_row("SOA:", soa_value)

    dns_table.add_row(
        "TXT:",
        display_value(common.get("TXT")),
    )

    console.print(dns_table)

    email_table = Table(
        title="Email Security",
        show_header=False,
    )
    email_table.add_column(
        "Record",
        style="magenta",
    )
    email_table.add_column("Value")

    email_table.add_row(
        "SPF:",
        dns_info.get("spf")
        or "[yellow]No SPF record found[/yellow]",
    )

    email_table.add_row(
        "DMARC:",
        dns_info.get("dmarc")
        or "[yellow]No DMARC record found[/yellow]",
    )

    console.print(email_table)

    whois_table = Table(
        title="WHOIS",
        show_header=False,
    )
    whois_table.add_column(
        "Field",
        style="magenta",
    )
    whois_table.add_column("Value")

    whois_table.add_row(
        "Created:",
        display_value(whois_info.get("created")),
    )

    whois_table.add_row(
        "Expires:",
        display_value(whois_info.get("expires")),
    )

    whois_table.add_row(
        "Registrar:",
        display_value(whois_info.get("registrar")),
    )

    whois_table.add_row(
        "Name servers:",
        display_value(whois_info.get("name_servers")),
    )

    whois_table.add_row(
        "Status:",
        display_value(whois_info.get("status")),
    )

    if whois_info.get("error"):
        whois_table.add_row(
            "Error:",
            whois_info["error"],
        )

    console.print(whois_table)


def print_json_report(report: dict[str, Any]) -> None:
    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Retrieve DNS and WHOIS "
            "information for a domain"
        )
    )

    parser.add_argument(
        "domain",
        help="Domain name to query, e.g. example.com",
    )

    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table or json",
    )

    args = parser.parse_args()
    report = build_report(args.domain)

    if args.format == "json":
        print_json_report(report)
    else:
        print_table_report(report)


if __name__ == "__main__":
    main()