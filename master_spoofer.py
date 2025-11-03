#!/usr/bin/env python3
# master_spoofer.py
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple



ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "gnss_data_generator"

DEFAULT_URL = "https://cddis.nasa.gov/archive/gnss/data/daily/2025/brdc/"
DEFAULT_DOWNLOADS = SRC / "download"


def parse_llh(llh: str) -> Tuple[float, float, float]:
    parts = [p.strip() for p in llh.split(",")]
    if len(parts) != 3:
        raise ValueError("Expected 'lat,lon,alt_m' (3 comma-separated numbers).")
    lat, lon, alt = map(float, parts)
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude out of range [-90, 90]: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude out of range [-180, 180]: {lon}")
    return lat, lon, alt


def ensure_llh(llh: str | None) -> str:
    if llh:
        parse_llh(llh)
        return llh
    while True:
        user = input('Enter coordinates as "lat,lon,alt_m" (e.g. 55.7558,37.6176,156): ').strip()
        try:
            parse_llh(user)
            return user
        except Exception as e:
            print(f"[ERROR] {e}. Try again.\n")


def run(cmd: list[str], verbose: bool) -> int:
    if verbose:
        print("[CMD]", " ".join([f'"{c}"' if " " in c else c for c in cmd]))
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Master runner: download latest BRDC and run gps-sdr-sim with given coordinates."
    )
    ap.add_argument("--url", default=DEFAULT_URL, help=f"CDDIS listing URL (default: {DEFAULT_URL})")
    ap.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS,
                    help=f"Download directory (default: {DEFAULT_DOWNLOADS})")
    ap.add_argument("--cookie", default=os.getenv("CDDIS_COOKIE"), help="Cookie header for CDDIS (or set CDDIS_COOKIE)")

    # Default GPS binary path
    default_gps_bin = (
        str((ROOT / "src" / "gnss_data_generator" / "gps-sdr-sim" / "gps-sdr-sim.exe"))
        if os.name == "nt"
        else "gps-sdr-sim"
    )
    ap.add_argument("--gps-bin", default=default_gps_bin,
                    help=f'Path to gps-sdr-sim binary (default: "{default_gps_bin}")')

    ap.add_argument("--llh", help='Coordinates "lat,lon,alt_m". If omitted, user will be prompted.')

    # Locations of your scripts
    ap.add_argument("--python-downloader", default=str(SRC / "downloader.py"),
                    help=f"Downloader script path (default: {SRC / 'downloader.py'})")
    ap.add_argument("--python-runner", default=str(SRC / "run_gps_spoof_sim.py"),
                    help=f"Runner script path (default: {SRC / 'run_gps_spoof_sim.py'})")

    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    ap.add_argument("--dry-run", action="store_true", help="Print commands only, do not execute")
    args = ap.parse_args()

    # --- Path setup ---
    downloads_dir = (args.downloads_dir if args.downloads_dir.is_absolute()
                     else (ROOT / args.downloads_dir).resolve())
    downloader_path = Path(args.python_downloader).resolve()
    runner_path = Path(args.python_runner).resolve()

    gps_bin = args.gps_bin
    if os.name == "nt":
        gps_bin = str((ROOT / gps_bin).resolve()) if Path(gps_bin).exists() else gps_bin

    if not SRC.exists():
        print(f"[FATAL] Expected folder not found: {SRC}", file=sys.stderr)
        sys.exit(2)

    # --- Coordinates ---
    try:
        llh = ensure_llh(args.llh)
    except Exception as e:
        print(f"[FATAL] Invalid coordinates: {e}", file=sys.stderr)
        sys.exit(2)

    downloads_dir.mkdir(parents=True, exist_ok=True)

    # --- Commands ---
    downloader_cmd = [
        sys.executable,
        str(downloader_path),
        args.url,
        "--decompress",
        "--out", str(downloads_dir),
    ]
    if args.cookie:
        downloader_cmd += ["--cookie", args.cookie]
    if args.verbose:
        downloader_cmd += ["-v"]

    runner_cmd = [
        sys.executable,
        str(runner_path),
        "--llh", llh,
        "--downloads-dir", str(downloads_dir),
        "--gps-bin", str(gps_bin),
       
    ]
    if args.verbose:
        runner_cmd += ["-v"]

    if args.dry_run:
        print("\n[Dry Run] Would execute:")
        print("  Downloader:", " ".join(downloader_cmd))
        print("  Runner:    ", " ".join(runner_cmd))
        sys.exit(0)

    print("\n[STEP 1/2] Downloading & decompressing newest BRDC file…")
    rc = run(downloader_cmd, verbose=args.verbose)
    if rc != 0:
        print(f"[FATAL] downloader exited with code {rc}", file=sys.stderr)
        sys.exit(rc)

    print("\n[STEP 2/2] Running gps-sdr-sim…")
    rc = run(runner_cmd, verbose=args.verbose)
    if rc != 0:
        print(f"[FATAL] gps runner exited with code {rc}", file=sys.stderr)
        sys.exit(rc)

    print("\n[OK] All done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
