#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import List, Set

import gzip
import shutil
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

USER_AGENT = "gnss-data-generator/brdc-filter/1.1"


def _session(cookie: str | None, verbose: bool) -> requests.Session:
    s = requests.Session()
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie.strip()
    s.headers.update(headers)

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.max_redirects = 15

    if verbose:
        print(f"[DEBUG] Session ready (UA={USER_AGENT})")
        if cookie:
            print("[DEBUG] Cookie header provided")
    return s


def _fetch_html(s: requests.Session, url: str, verbose: bool) -> str:
    r = s.get(url, allow_redirects=True, timeout=60)
    if verbose:
        print(f"[DEBUG] GET {url} -> {r.status_code} ({r.url})")
    r.raise_for_status()
    return r.text


def _collect_links(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [a["href"].strip() for a in soup.find_all("a", href=True)]


def _filter_brdc_links(hrefs: List[str], verbose: bool = False) -> Set[str]:
    """Return only hrefs matching brdcXXXX.YYn.gz where YY is current year."""
    current_year = dt.date.today().year % 100  # e.g., 2025 -> 25
    pattern = re.compile(rf"^brdc\d{{4}}\.\d{{2}}n\.gz$", re.IGNORECASE)

    if verbose:
        print(f"[DEBUG] Filtering for current-year pattern (YY={current_year:02d})")

    result: Set[str] = set()
    for h in hrefs:
        if pattern.match(h):
            yy = int(h.split(".")[1][:2])
            if yy == current_year:
                result.add(h)
                if verbose:
                    print(f"[DEBUG] Match: {h}")
    return result


def _download(s: requests.Session, url: str, out_dir: Path, verbose: bool) -> Path:
    """Download a file to out_dir and return its local path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1]
    dest = out_dir / filename

    if verbose:
        print(f"[DEBUG] Downloading {url} -> {dest}")

    with s.get(url, stream=True, allow_redirects=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    if verbose:
        print(f"[DEBUG] Saved {dest} ({os.path.getsize(dest):,} bytes)")
    return dest


def _maybe_decompress_gz(path: Path, verbose: bool) -> Path | None:
    """
    If `path` ends with .gz, decompress it to the same directory and return the new Path.
    Returns None if not .gz or on recoverable failure.
    """
    if path.suffix.lower() != ".gz":
        if verbose:
            print(f"[DEBUG] Not decompressing {path.name} (not .gz)")
        return None

    out_path = path.with_suffix("")  # drop .gz
    if verbose:
        print(f"[DEBUG] Decompressing {path.name} -> {out_path.name}")

    try:
        with gzip.open(path, "rb") as src, open(out_path, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1 << 20)  # stream in 1MB chunks
    except gzip.BadGzipFile as e:
        print(f"[WARN] Bad gzip file: {path.name}: {e}")
        return None
    except Exception as e:
        print(f"[WARN] Failed to decompress {path.name}: {e}")
        return None

    if verbose:
        try:
            size = os.path.getsize(out_path)
            print(f"[DEBUG] Decompressed size: {size:,} bytes")
        except Exception:
            pass
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Fetch hrefs, keep brdcXXXX.YYn.gz for current year, download newest, and optionally decompress."
    )
    ap.add_argument(
        "url",
        help="Base URL (e.g., https://cddis.nasa.gov/archive/gnss/data/daily/2025/brdc/)",
    )
    ap.add_argument(
        "--cookie",
        type=str,
        default=os.getenv("CDDIS_COOKIE"),
        help="Raw Cookie header (or set CDDIS_COOKIE)",
    )
    ap.add_argument("--out", type=Path, default=Path("./downloads"), help="Download directory")
    ap.add_argument("--decompress", action="store_true", help="Decompress .gz after download")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    s = _session(args.cookie, verbose=args.verbose)
    html = _fetch_html(s, args.url, verbose=args.verbose)
    hrefs = _collect_links(html)

    brdc_set = _filter_brdc_links(hrefs, verbose=args.verbose)

    if not brdc_set:
        print("No matching brdcXXXX.YYn.gz files found for current year.")
        sys.exit(0)

    print(f"Found {len(brdc_set)} matching file(s).")
    target_files = sorted(brdc_set)
    newest = target_files[-1]
    print(f"Newest file: {newest}")

    file_url = f"{args.url.rstrip('/')}/{newest}"
    print(f"Downloading: {file_url}")

    dest = _download(s, file_url, args.out, verbose=args.verbose)
    print(f"Saved to: {dest.resolve()}")

    if args.decompress:
        outp = _maybe_decompress_gz(dest, verbose=args.verbose)
        if outp:
            print(f"Decompressed to: {outp.resolve()}")
        else:
            print("Skipping decompression (not .gz or failed).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
