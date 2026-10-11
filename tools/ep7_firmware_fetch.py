#!/usr/bin/env python3
"""Experimental read-only download of official E-P7 update payload.

Community-protocol experiment, not an OM SYSTEM tool. No camera is connected.
No firmware is installed or modified. Only use a serial number you are
entitled to use; do not publish the serial or the downloaded OEM file.
"""
import argparse
import getpass
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ENDPOINT = "https://fw01.om-digitalsolutions.net/ww_inform/fcache.do"
VALID_DOMAINS = ("om-digitalsolutions.net", "olympus-imaging.com")


def allowed_vendor_url(url: str, *, https_only=True) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    approved = any(host == d or host.endswith("." + d) for d in VALID_DOMAINS)
    return approved and parsed.scheme in (("https",) if https_only else ("https", "http"))


def build_request(serial: str) -> bytes:
    # Structure based on a public 2026 community protocol example; E142 = PEN E-P7.
    root = ET.Element("firmware_demand")
    fields = (
        ("revision", "0001"), ("mac_address", "00-00-00-00-80-D6"),
        ("time", time.strftime("%Y%m%d%H%M%S")), ("language", "ENU"),
        ("application", "FWUT"), ("type", "0000"),
        ("version", "00005000"), ("os", "WIN"), ("country_code", "0001"),
    )
    for k, v in fields:
        ET.SubElement(root, k).text = v
    hardwares = ET.SubElement(root, "hardwares")
    ET.SubElement(hardwares, "firmup_mode").text = "0"
    hardware = ET.SubElement(hardwares, "hardware_info")
    ET.SubElement(hardware, "hard_code").text = "OLYE142000000000"
    ET.SubElement(hardware, "firmware_version").text = "00001000"
    ET.SubElement(hardware, "serial_no").text = serial
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, default=Path("~/ep7-firmware").expanduser())
    ap.add_argument("--allow-http", action="store_true", help="Allow HTTP on verified vendor hosts (not preferred)")
    args = ap.parse_args()
    serial = getpass.getpass("E-P7 camera serial (entered locally; not stored): ").strip()
    if not serial or len(serial) > 60:
        print("No plausible serial entered; no request made.", file=sys.stderr)
        return 2
    request = urllib.request.Request(
        ENDPOINT, data=build_request(serial), method="POST",
        headers={"User-Agent": "Olympus", "Content-Type": "text/xml; Charset=UTF-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as reply:
            response = reply.read(1024 * 1024)
        root = ET.fromstring(response)
        url = (root.findtext(".//url") or "").strip()
        filename = (root.findtext(".//file_name") or "").strip()
        if not url:
            print("Official service returned no firmware URL. Stop; do not guess URLs.")
            print("Response root tag:", root.tag)
            return 3
        if not allowed_vendor_url(url, https_only=not args.allow_http):
            print("Refusing a nonapproved download URL (unexpected host or scheme).", file=sys.stderr)
            return 4
        print("Vendor download host:", urllib.parse.urlsplit(url).hostname)
        print("Vendor-reported filename:", os.path.basename(filename) if filename else "(not provided)")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output = args.output_dir / "E142_EP7_firmware_download.BIN"
        if output.exists():
            print("Output exists; refusing to overwrite:", output, file=sys.stderr)
            return 5
        digest = hashlib.sha256()
        count = 0
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Olympus"}), timeout=45) as reply:
            if not allowed_vendor_url(reply.url, https_only=not args.allow_http):
                raise RuntimeError("Download redirected to an unapproved host")
            with tempfile.NamedTemporaryFile(mode="wb", dir=args.output_dir, prefix=".ep7_partial_", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                try:
                    while True:
                        block = reply.read(1024 * 1024)
                        if not block:
                            break
                        count += len(block)
                        if count > 512 * 1024 * 1024:
                            raise RuntimeError("Unexpected file exceeds 512 MiB")
                        tmp.write(block)
                        digest.update(block)
                except BaseException:
                    tmp_path.unlink(missing_ok=True)
                    raise
        with tmp_path.open("rb") as f:
            head = f.read(32).lstrip().lower()
        if count < 1024 * 1024 or head.startswith((b"<html", b"<!doctype", b"<?xml")):
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError("Returned data is too small or looks like HTML/XML, not a firmware image")
        tmp_path.rename(output)
        print("Saved:", output)
        print("Bytes:", count)
        print("SHA-256:", digest.hexdigest())
        print("This proves successful download ONLY. It does not verify E-P7 authenticity, format, or flashing safety.")
        print("Do not place this file on a camera or in a public GitHub repository.")
        return 0
    except Exception as exc:
        print("Download experiment failed:", type(exc).__name__, str(exc)[:250], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
