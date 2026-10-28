import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from .exporter import Exporter
from .report import report
from .auth import RefreshingClient


def date_arg(value):
    try: return date.fromisoformat(value)
    except ValueError: raise argparse.ArgumentTypeError("Use YYYY-MM-DD") from None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="garmin-export")
    parser.add_argument("--output", default="output")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth-test"); sub.add_parser("report"); sub.add_parser("status")
    full = sub.add_parser("full")
    full.add_argument("--start-date", type=date_arg, default=date.today()-timedelta(days=3650))
    full.add_argument("--end-date", type=date_arg, default=date.today())
    full.add_argument("--resume", action="store_true", help="Completed, verified queries are always reused")
    snap = sub.add_parser("snapshot"); snap.add_argument("--date", type=date_arg, required=True)
    for p in (full, snap):
        p.add_argument("--categories", help="Comma-separated endpoint category names")
        p.add_argument("--delay", type=float, default=0.25)
        p.add_argument("--batch-days", type=int, default=30)
    args = parser.parse_args(argv)
    if args.command in ("report", "status"):
        result = report(args.output)
        print(result["assessment"]); print(result["query_status_counts"]); return 0
    if args.command != "auth-test":
        start = args.date if args.command == "snapshot" else args.start_date
        end = args.date if args.command == "snapshot" else args.end_date
        if start > end or args.delay < 0 or args.batch_days < 1: parser.error("Invalid date range, delay, or batch size")
    try:
        from dotenv import load_dotenv
        from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator, resolve_api_key
        load_dotenv()
        key = resolve_api_key()
        with PersonalApiAuthenticator() as auth:
            token = auth.obtain_token(key)
            with GarminPersonalApiClient(token.access_token) as raw_client:
                client = RefreshingClient(raw_client, auth, key, token)
                if args.command == "auth-test":
                    client.get_user_profile_settings(); print("Authentication and profile request succeeded."); return 0
                exporter = Exporter(client, args.output, delay=args.delay)
                try: exporter.run(start, end, args.categories.split(",") if args.categories else None, args.batch_days)
                finally: result = report(args.output)
        print(f"Reports: {Path(args.output).resolve() / 'reports'}")
        return 1 if any(k != "success" and v for k, v in result["query_status_counts"].items()) or result["integrity_failures"] else 0
    except KeyboardInterrupt:
        print("Interrupted; completed requests remain checkpointed.", file=sys.stderr); return 130
    except Exception as exc:
        print(f"Export could not start or finish ({type(exc).__name__}). Check credentials, connectivity, and configuration.", file=sys.stderr); return 1

if __name__ == "__main__": sys.exit(main())
