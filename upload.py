#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

CONFIG_FILE = Path(__file__).parent / "config.yaml"
LOG_FILE = Path(__file__).parent / "upload_log.json"

log = logging.getLogger("scenenzb")

ERROR_MESSAGES = {
    400: "Bad request — invalid NZB, blocked name, or missing file",
    401: "Unauthorized — check your API key",
    403: "Forbidden — insufficient upload privileges",
    405: "Method not allowed",
    409: "Duplicate — this NZB has already been uploaded",
    429: "Rate limited — wait before retrying",
    500: "Server error",
}


def load_config():
    if not CONFIG_FILE.exists():
        log.error("Config file not found at %s", CONFIG_FILE)
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
    base_url = config.get("base_url", "").rstrip("/")
    api_path = config.get("api_path", "").rstrip("/")
    config["_api_url"] = f"{base_url}{api_path}"
    config["_site_url"] = base_url
    return config


def load_upload_log():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return []


def save_upload_log(entries):
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def find_companion(nzb_path, suffix):
    """Look for a companion file matching the nzb stem with the given suffix."""
    candidate = nzb_path.with_suffix(suffix)
    if candidate.is_file():
        return candidate
    return None


def upload_nzb(filepath, api_key, category, config, mediainfo_path=None, nfo_path=None):
    filepath = Path(filepath)

    # Auto-detect companion files if not explicitly provided
    if mediainfo_path is None:
        mediainfo_path = find_companion(filepath, ".xml")
    if nfo_path is None:
        nfo_path = find_companion(filepath, ".nfo")

    files = {"file": (filepath.name, open(filepath, "rb"), "application/octet-stream")}
    if mediainfo_path:
        mediainfo_path = Path(mediainfo_path)
        files["mediainfo"] = (mediainfo_path.name, open(mediainfo_path, "rb"), "application/octet-stream")
        log.info("  + MediaInfo: %s", mediainfo_path.name)
    if nfo_path:
        nfo_path = Path(nfo_path)
        files["nfo"] = (nfo_path.name, open(nfo_path, "rb"), "application/octet-stream")
        log.info("  + NFO: %s", nfo_path.name)

    data = {}
    if category is not None:
        data["cat"] = category

    resp = requests.post(
        f"{config['_api_url']}/nzb",
        headers={"X-API-Key": api_key},
        files=files,
        data=data,
        timeout=120,
    )

    entry = {
        "file": str(filepath.resolve()),
        "filename": filepath.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": resp.status_code,
    }

    if resp.status_code == 201:
        body = resp.json()
        release = body.get("release", {})
        guid = release.get("guid", "")
        entry["guid"] = guid
        entry["release_id"] = release.get("id")
        entry["category_id"] = release.get("category_id")
        entry["release_name"] = release.get("name")
        entry["url"] = f"{config['_site_url']}/releases/{guid}" if guid else None
        entry["status"] = "ok"
        log.info("Uploading: %s ... OK", filepath.name)
        log.info("  Link: %s", entry["url"])
    elif resp.status_code == 409:
        entry["status"] = "skipped"
        log.warning("Skipping: %s", filepath.name)
        log.warning("  Detail: NZB has already been uploaded")
    else:
        msg = ERROR_MESSAGES.get(resp.status_code, f"HTTP {resp.status_code}")
        try:
            detail = resp.json().get("error", resp.text)
        except Exception:
            detail = resp.text
        entry["status"] = "error"
        entry["error"] = f"{msg}: {detail}"
        log.error("Skipping: %s", filepath.name)
        log.error("  Detail: %s", msg)
        if detail:
            log.error("  %s", detail)

    return entry


def collect_nzb_files(path):
    path = Path(path)
    if path.is_file():
        if path.suffix.lower() != ".nzb":
            log.warning("%s is not an .nzb file, uploading anyway", path)
        return [path]
    elif path.is_dir():
        nzbs = sorted(path.glob("*.nzb"))
        if not nzbs:
            log.error("No .nzb files found in %s", path)
            sys.exit(1)
        return nzbs
    else:
        log.error("%s does not exist", path)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SceneNZBs NZB Uploader")
    parser.add_argument("-path", required=True, help="Path to an .nzb file or a folder containing .nzb files")
    parser.add_argument("-mediainfo", default=None, help="Path to MediaInfo XML file (single-file mode only)")
    parser.add_argument("-nfo", default=None, help="Path to NFO file (single-file mode only)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    config = load_config()
    api_key = config.get("api_key", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        log.error("Set your API key in config.yaml")
        sys.exit(1)

    category = config.get("category", -1)
    files = collect_nzb_files(args.path)
    upload_entries = load_upload_log()

    log.info("Found %d file(s) to upload\n", len(files))

    ok = 0
    skipped = 0
    fail = 0
    for f in files:
        entry = upload_nzb(f, api_key, category, config, args.mediainfo, args.nfo)
        upload_entries.append(entry)
        save_upload_log(upload_entries)
        if entry["status"] == "ok":
            ok += 1
        elif entry["status"] == "skipped":
            skipped += 1
        else:
            fail += 1

    log.info("\nDone: %d uploaded, %d skipped, %d failed", ok, skipped, fail)
    log.info("Log: %s", LOG_FILE)


if __name__ == "__main__":
    main()
