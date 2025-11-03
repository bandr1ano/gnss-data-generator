# GNSS Data Generator — Project Documentation

## Overview

This project automates fetching the latest **GNSS BRDC** navigation file(s) and uses them to generate a **GPS baseband IQ file** 
(e.g. `gps.bin`) using the external tool **`gps-sdr-sim`**. 
It is useful for **offline GNSS simulation** and **lab-only testing**.

> ⚠️ **Legal & safety**: Transmitting spoofed GNSS signals over the air is illegal in many jurisdictions 
> and can endanger people and infrastructure. Use only for **offline generation** 
> or playback inside shielded test setups where you are authorized.

## Layout

```
GNSS Data Generator/
├─ master_spoofer.py                     # Orchestrates: download latest BRDC + run gps-sdr-sim
└─ src/gnss_data_generator/
   ├─ cli.py                             # Simple "gnss-dl" downloader CLI
   ├─ downloader.py                      # Finds & downloads latest BRDC; can decompress .gz
   └─ run_gps_spoof_sim.py               # Wrapper to call gps-sdr-sim with coords/nav-file
```

The project also contains `.venv/` which you **should not commit**. Prefer a fresh virtual environment instead.

## Requirements

- **Python** 3.10+ (3.11/3.12 recommended)
- Python packages: `requests`, `beautifulsoup4`
- External binary: **`gps-sdr-sim`** (not included). Build and place its binary on your PATH, or note its full path.

A minimal `requirements_min.txt` is provided alongside this README for convenience.

## Quick Start

### 1) Create and activate a virtual environment

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (Powershell)
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

### 2) Install dependencies
```bash
pip install -r requirements_min.txt
```
*(Or)*
```bash
pip install requests beautifulsoup4
```

### 3) Get/build `gps-sdr-sim`

- Upstream project: https://github.com/osqzss/gps-sdr-sim (or maintained forks)
- Build it and make sure the `gps-sdr-sim` binary is available on your PATH, or note its absolute path for the `--gps-bin` option below.

### 4) Run the downloader

The basic downloader CLI lives at `src/gnss_data_generator/cli.py` and supports:
- `--year` (defaults to the current year)
- `--out` (download folder, defaults to `./downloads`)
- `--decompress` (if the downloaded file is `.gz`, also write an uncompressed copy)

Run either as a module or plain script:

```bash
python -m gnss_data_generator.cli --out downloads --decompress
```

This should create something like:
```
downloads/
  brdcNNNN.25n.gz   # and optionally brdcNNNN.25n after --decompress
```

### 5) Generate GPS baseband with `run_gps_spoof_sim.py`

This wrapper calls `gps-sdr-sim` and wires up common parameters. Example:

```bash
python -m gnss_data_generator.run_gps_spoof_sim \
  --llh "37.9838,23.7275,60" \
  --search-dir downloads
```

Or with explicit file and output name:

```bash
python -m gnss_data_generator.run_gps_spoof_sim \
  --llh "37.9838,23.7275,60" \
  --nav-file downloads/brdc1230.25n \
  --out gps_athens.bin
```

### 6) One-shot orchestrator: `master_spoofer.py`

Example:

```bash
 python master_spoofer.py --llh "55.7558,37.6176,156" 
```

## Developer Guide

- Source lives under `src/gnss_data_generator`
- Run modules with `python -m gnss_data_generator.<module>` after ensuring `src/` is on `PYTHONPATH`.
- You can later add a `pyproject.toml` with a `gnss-dl` CLI entry.

## Troubleshooting

- **ImportError** → run modules with `python -m`
- **403 from CDDIS** → follow the steps on `HOW_TO_GET_AND_SET_CDDIS_COOKIE.md`
- **gps-sdr-sim not found** → build it and add to PATH or use `--gps-bin`
- **Do not transmit** → Only use offline or in authorized shielded environments

## Clean Repo Tips

- Remove `.venv/` before committing or zipping
- Include only `README.md`, `requirements.txt`, and optionally `pyproject.toml`
- Consider CI tests that run `--dry-run` mode

---
