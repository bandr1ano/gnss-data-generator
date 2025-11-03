from __future__ import annotations
import argparse
from pathlib import Path
import datetime as dt

from .downloader import _make_session, find_latest_brdc, download, maybe_decompress_gz

def main() -> None:
    ap = argparse.ArgumentParser(prog="gnss-dl", description="GNSS BRDC downloader")
    ap.add_argument("--year", type=int, default=dt.date.today().year)
    ap.add_argument("--out", type=Path, default=Path("./downloads"))
    ap.add_argument("--decompress", action="store_true")
    args = ap.parse_args()

    s = _make_session()
    d, name, url = find_latest_brdc(s, args.year)
    dest = download(s, url, args.out)
    print(f"Downloaded {name} for {d} → {dest.resolve()}")
    if args.decompress and dest.suffix.lower() == ".gz":
        outp = maybe_decompress_gz(dest)
        print(f"Decompressed → {outp.resolve()}")
