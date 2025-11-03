#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import shutil

# Defaults you can tweak
DEFAULT_OUTPUT = "gps.bin"
DEFAULT_BITS = "8"  # -b 8
DEFAULT_TIME = "now"  # -T now

def _parse_llh(llh: str) -> Tuple[float, float, float]:
    """
    Parse "lat,lon,alt" string into floats.
    Altitude assumed in meters (gps-sdr-sim expects meters).
    """
    try:
        parts = [p.strip() for p in llh.split(",")]
        if len(parts) != 3:
            raise ValueError("Expected exactly three comma-separated numbers: lat,lon,alt")
        lat, lon, alt = map(float, parts)
    except Exception as e:
        raise ValueError(f"Invalid --llh '{llh}': {e}")

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of range [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of range [-180, 180]: {lon}")

    return lat, lon, alt

def _find_latest_nav(downloads_dir: Path) -> Optional[Path]:
    """
    Pick the newest unzipped RINEX2 BRDC nav file in downloads_dir.
    Heuristic: extension-less files named like 'brdc####.??n' (e.g., brdc2880.25n)
    """
    if not downloads_dir.exists():
        return None

    candidates = []
    for p in downloads_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name.lower()
        # very simple pattern check
        if name.startswith("brdc") and name.endswith("n") and "." in name and not name.endswith(".gz"):
            candidates.append(p)

    if not candidates:
        return None

    # Newest by mtime
    candidates.sort(key=lambda x: x.stat().st_mtime)
    return candidates[-1]

def _require_binary(name: str, custom_path: Optional[str] = None) -> str:
    """
    Ensure gps-sdr-sim binary exists; return an executable path.
    """
    if custom_path:
        exe = Path(custom_path).expanduser().resolve()
        if not exe.exists():
            raise FileNotFoundError(f"gps-sdr-sim not found at: {exe}")
        if not os.access(exe, os.X_OK):
            raise PermissionError(f"gps-sdr-sim is not executable: {exe}")
        return str(exe)

    found = shutil.which(name)
    if not found:
        raise FileNotFoundError(
            "gps-sdr-sim not found in PATH. "
            "Install it or pass --gps-bin /path/to/gps-sdr-sim"
        )
    return found

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run gps-sdr-sim with user coordinates and a BRDC nav file."
    )
    ap.add_argument(
        "--llh",
        required=True,
        help="Coordinates as 'lat,lon,alt_m' (e.g., '55.7558,37.6176,156').",
    )
    ap.add_argument(
        "--nav-file",
        type=Path,
        default=None,
        help="Path to unzipped RINEX2 nav file (e.g., brdc1220.25n). "
             "If omitted, the script tries to pick the newest in --downloads-dir.",
    )
    ap.add_argument(
        "--downloads-dir",
        type=Path,
        default=Path("./downloads"),
        help="Directory to search for newest nav file when --nav-file is omitted.",
    )
    ap.add_argument(
        "--gps-bin",
        type=str,
        default=None,
        help="Path to gps-sdr-sim binary (if not in PATH).",
    )
    # Fixed by default, but overridable if you ever need to
    ap.add_argument("--bits", "-b", default=DEFAULT_BITS, help="gps-sdr-sim -b value (default: 8)")
    ap.add_argument("--out", "-o", type=Path, default=Path(DEFAULT_OUTPUT), help="Output file (default: gps.bin)")
    ap.add_argument("--time", "-T", default=DEFAULT_TIME, help="gps-sdr-sim -T value (default: now)")
    ap.add_argument("--dry-run", action="store_true", help="Print the command and exit without running.")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = ap.parse_args()

    # Parse and validate LLH
    lat, lon, alt = _parse_llh(args.llh)

    # Locate nav file
    nav = args.nav_file
    if nav is None:
        nav = _find_latest_nav(args.downloads_dir)
        if nav is None:
            print(
                "ERROR: No nav file provided and none found in downloads directory. "
                "Pass --nav-file or place your RINEX nav (e.g., brdc*.n) in ./downloads.",
                file=sys.stderr,
            )
            sys.exit(2)
    nav = nav.expanduser().resolve()
    if not nav.exists():
        print(f"ERROR: Nav file does not exist: {nav}", file=sys.stderr)
        sys.exit(2)

    # Ensure gps-sdr-sim is available
    gps_bin = _require_binary("gps-sdr-sim", custom_path=args.gps_bin)

    # Compose command
    cmd = [
        gps_bin,
        "-b", str(args.bits),
        "-e", str(nav),
        "-l", f"{lat},{lon},{alt}",
        "-o", str(args.out),
        "-T", str(args.time),
        "-d", "300",   
    ]

    if args.verbose or args.dry_run:
        print("[INFO] Command:", " ".join(map(str, cmd)))
        print(f"[INFO] Using nav: {nav.name}")
        print(f"[INFO] Output: {args.out.resolve()}")
        print(f"[INFO] LLH: lat={lat}, lon={lon}, alt_m={alt}")
        print(f"[INFO] Time: {args.time}")

    if args.dry_run:
        return

    # Run it
    try:
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            print(f"gps-sdr-sim exited with code {proc.returncode}", file=sys.stderr)
            sys.exit(proc.returncode)
    except FileNotFoundError:
        print("ERROR: gps-sdr-sim executable not found.", file=sys.stderr)
        sys.exit(127)

    if args.verbose:
        print("[INFO] Done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
