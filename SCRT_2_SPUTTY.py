#!/usr/bin/env python3
"""
SCRT_2_SPUTTY.py
Convert a SecureCRT XML session export to a SuperPutty XML import file.

Author  : Jeff Fry
Blog    : https://fryguy.net
Version : 1.0.0
Date    : 2026-04-14

Version History:
    1.0.0 (2026-04-14) - Initial release

Usage:
    python SCRT_2_SPUTTY.py <SecureCRT_Sessions.xml> [output.xml]

If no output file is specified, the result is written to
'SuperPutty_Sessions.xml' in the current directory.

Supported SecureCRT protocols and their SuperPutty mapping:
    SSH2        -> SSH
    SSH1        -> SSH
    Telnet      -> Telnet
    TelnetSSL   -> Telnet (no native TLS-Telnet in SuperPutty)
    RDP         -> RDP
    Serial      -> (skipped — SuperPutty has no serial proto)
    Local Shell -> (skipped — no equivalent)
    SFTP        -> SSH  (SuperPutty uses SSH for SFTP-like sessions)

Folder structure:
    SecureCRT organises sessions in nested <key> elements.  Any key that
    contains sub-keys (and is NOT itself a session) is treated as a folder.
    The folder path is prepended to the session name so that SuperPutty's
    flat session list still communicates the hierarchy, e.g.:
        "Datacenter/Core Switches/sw-core-01"
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ---------------------------------------------------------------------------
# Protocol mapping
# ---------------------------------------------------------------------------
PROTO_MAP = {
    "SSH2":       "SSH",
    "SSH1":       "SSH",
    "SSH":        "SSH",
    "Telnet":     "Telnet",
    "TelnetSSL":  "Telnet",
    "RDP":        "RDP",
    "SFTP":       "SSH",
}

# Protocols we silently skip (no sensible SuperPutty equivalent)
SKIP_PROTOS = {"Serial", "Local Shell", "TAPI", "Raw"}

# Default values used when SecureCRT session fields are absent/empty/"None"
DEFAULT_PORT_SSH    = 22
DEFAULT_PORT_TELNET = 23
DEFAULT_PORT_RDP    = 3389
DEFAULT_PUTTY_SESSION = "Default Settings"

# SecureCRT "Default*" sessions are template stubs — skip them by default
SKIP_SESSION_NAMES = {"Default", "Default_LocalShell", "Default_RDP",
                      "Default_Serial", "Default_SFTP"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_val(key_elem, tag, name):
    """Return the text of the first child <tag name='name'> or None."""
    for child in key_elem:
        if child.tag == tag and child.attrib.get("name") == name:
            text = child.text
            if text and text.strip() and text.strip().lower() != "none":
                return text.strip()
    return None


def _is_session(key_elem):
    """Return True when the key element represents a real session."""
    val = _get_val(key_elem, "dword", "Is Session")
    return val == "1"


def _default_port(proto_superputty):
    return {
        "SSH":    DEFAULT_PORT_SSH,
        "Telnet": DEFAULT_PORT_TELNET,
        "RDP":    DEFAULT_PORT_RDP,
    }.get(proto_superputty, DEFAULT_PORT_SSH)


def _sanitize_session_id(path):
    """Turn a folder/session path into a valid SuperPutty SessionId string."""
    # SuperPutty uses '/' as path separator in SessionId
    return path.replace("\\", "/")


# ---------------------------------------------------------------------------
# Core traversal
# ---------------------------------------------------------------------------

def extract_sessions(key_elem, folder_path=""):
    """
    Recursively walk a <key> element tree and yield dicts for each session.

    folder_path is the human-readable parent path, e.g. "Datacenter/Core".
    """
    sessions = []

    for child in key_elem:
        if child.tag != "key":
            continue

        child_name = child.attrib.get("name", "unknown")

        if _is_session(child):
            # ---- It's a session leaf ----
            if child_name in SKIP_SESSION_NAMES:
                continue  # skip template stubs

            proto_crt = _get_val(child, "string", "Protocol Name") or "SSH2"

            if proto_crt in SKIP_PROTOS:
                print(f"  [skip] '{child_name}' — protocol '{proto_crt}' "
                      "has no SuperPutty equivalent", file=sys.stderr)
                continue

            proto_sp = PROTO_MAP.get(proto_crt)
            if proto_sp is None:
                print(f"  [skip] '{child_name}' — unknown protocol "
                      f"'{proto_crt}'", file=sys.stderr)
                continue

            hostname = _get_val(child, "string", "Hostname") or ""
            username = _get_val(child, "string", "Username") or ""

            # Port: SSH2 uses "[SSH2] Port", Telnet uses "[Telnet] Port",
            # RDP uses "[RDP] Port" — fall back to protocol default.
            port_raw = (
                _get_val(child, "dword", "[SSH2] Port")
                or _get_val(child, "dword", "[Telnet] Port")
                or _get_val(child, "dword", "[RDP] Port")
                or _get_val(child, "dword", "Port")
            )
            try:
                port = int(port_raw)
            except (TypeError, ValueError):
                port = _default_port(proto_sp)

            # Build the display name and session id
            if folder_path:
                display_name = f"{folder_path}/{child_name}"
            else:
                display_name = child_name

            session_id = _sanitize_session_id(display_name)

            sessions.append({
                "SessionId":     session_id,
                "SessionName":   display_name,
                "Host":          hostname,
                "Port":          port,
                "Proto":         proto_sp,
                "Username":      username,
                "PuttySession":  DEFAULT_PUTTY_SESSION,
                "ImageKey":      "computer",
                "ExtraArgs":     "",
                "SPSLFileName":  "",
                "RemotePath":    "",
                "LocalPath":     "",
            })

        else:
            # ---- It's a folder — recurse ----
            new_path = f"{folder_path}/{child_name}" if folder_path else child_name
            sessions.extend(extract_sessions(child, folder_path=new_path))

    return sessions


# ---------------------------------------------------------------------------
# XML generation
# ---------------------------------------------------------------------------

def build_superputty_xml(sessions):
    """Return a prettily-formatted SuperPutty XML string."""
    root = ET.Element("ArrayOfSessionData")
    root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    for s in sessions:
        sd = ET.SubElement(root, "SessionData")
        sd.set("SessionId",    s["SessionId"])
        sd.set("SessionName",  s["SessionName"])
        sd.set("ImageKey",     s["ImageKey"])
        sd.set("Host",         s["Host"])
        sd.set("Port",         str(s["Port"]))
        sd.set("Proto",        s["Proto"])
        sd.set("PuttySession", s["PuttySession"])
        sd.set("Username",     s["Username"])
        sd.set("ExtraArgs",    s["ExtraArgs"])
        sd.set("SPSLFileName", s["SPSLFileName"])
        sd.set("RemotePath",   s["RemotePath"])
        sd.set("LocalPath",    s["LocalPath"])

    # Pretty-print via minidom
    raw = ET.tostring(root, encoding="unicode")
    parsed = minidom.parseString(raw)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def convert(input_path, output_path):
    print(f"Reading  : {input_path}")

    try:
        tree = ET.parse(input_path)
    except ET.ParseError as exc:
        print(f"ERROR: Could not parse '{input_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()

    # SecureCRT exports start with <VanDyke> and sessions live under
    # <key name="Sessions">.  Handle both a raw export and a file that
    # already has the sessions key as root.
    sessions_key = root.find('.//key[@name="Sessions"]')
    if sessions_key is None:
        # Maybe the root IS the Sessions key
        if root.tag == "key" and root.attrib.get("name") == "Sessions":
            sessions_key = root
        else:
            print("ERROR: Could not find <key name=\"Sessions\"> in the input "
                  "file.  Is this a valid SecureCRT XML export?", file=sys.stderr)
            sys.exit(1)

    sessions = extract_sessions(sessions_key)

    if not sessions:
        print("WARNING: No convertible sessions found.", file=sys.stderr)

    xml_str = build_superputty_xml(sessions)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(xml_str)

    print(f"Converted: {len(sessions)} session(s)")
    print(f"Written  : {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a SecureCRT XML session export to SuperPutty XML.")
    parser.add_argument("input",
                        help="Path to SecureCRT XML export file")
    parser.add_argument("output", nargs="?",
                        default="SuperPutty_Sessions.xml",
                        help="Output SuperPutty XML file "
                             "(default: SuperPutty_Sessions.xml)")
    args = parser.parse_args()
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
