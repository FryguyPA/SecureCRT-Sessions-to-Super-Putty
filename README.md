# SCRT_2_SPUTTY

Convert a **SecureCRT** XML session export into a **SuperPutty** XML import file.

> Author: Jeff Fry — [fryguy.net](https://fryguy.net)  
> Version: 1.0.0 | 2026-04-14

---

## Overview

If you're migrating from SecureCRT to SuperPutty (or just want a copy of your sessions in SuperPutty), this script does the heavy lifting. It parses the SecureCRT XML export, maps each session to the SuperPutty format, and writes a ready-to-import XML file — no manual re-entry required.

---

## Requirements

- Python 3.6 or later
- No third-party packages — uses the Python standard library only (`xml`, `argparse`, `sys`)

---

## Exporting Sessions from SecureCRT

1. Open SecureCRT
2. Go to **Tools → Export Settings...**
3. Select **Sessions** and choose **XML** as the export format
4. Save the file (e.g. `SecureCRT_Sessions.xml`)

---

## Usage

```bash
python SCRT_2_SPUTTY.py <input_file> [output_file]
```

| Argument | Required | Description |
|---|---|---|
| `input_file` | Yes | Path to the SecureCRT XML export |
| `output_file` | No | Path for the SuperPutty XML output (default: `SuperPutty_Sessions.xml`) |

**Examples:**

```bash
# Use default output filename
python SCRT_2_SPUTTY.py SecureCRT_Sessions.xml

# Specify an output path
python SCRT_2_SPUTTY.py SecureCRT_Sessions.xml C:\Users\jeff\SuperPutty_Import.xml
```

**Sample output:**

```
Reading  : SecureCRT_Sessions.xml
Converted: 42 session(s)
Written  : SuperPutty_Sessions.xml
```

---

## Importing into SuperPutty

1. Open SuperPutty
2. Go to **File → Import Sessions → From XML File...**
3. Select the generated XML file
4. Your sessions will appear in the session list

---

## Protocol Mapping

| SecureCRT Protocol | SuperPutty Protocol |
|---|---|
| SSH2 | SSH |
| SSH1 | SSH |
| Telnet | Telnet |
| TelnetSSL | Telnet |
| RDP | RDP |
| SFTP | SSH |
| Serial | *(skipped)* |
| Local Shell | *(skipped)* |
| TAPI | *(skipped)* |
| Raw | *(skipped)* |

Protocols with no SuperPutty equivalent (Serial, Local Shell, TAPI, Raw) are skipped and reported to the console.

---

## Folder / Hierarchy Support

SecureCRT organises sessions in nested folder groups. SCRT_2_SPUTTY preserves this hierarchy by prepending the folder path to each session name, since SuperPutty uses a flat session list. For example, a SecureCRT session at:

```
Sessions/
  Datacenter/
    Core Switches/
      sw-core-01
```

...becomes a SuperPutty session named:

```
Datacenter/Core Switches/sw-core-01
```

---

## What Gets Skipped

The following are automatically filtered and will not appear in the output:

- SecureCRT built-in template stubs: `Default`, `Default_RDP`, `Default_Serial`, `Default_LocalShell`, `Default_SFTP`
- Any session using a protocol with no SuperPutty equivalent (see table above)

---

## Default Port Fallback

If a session in SecureCRT has no port defined, the following defaults are used:

| Protocol | Default Port |
|---|---|
| SSH | 22 |
| Telnet | 23 |
| RDP | 3389 |

---

## Version History

| Version | Date | Notes |
|---|---|---|
| 1.0.0 | 2026-04-14 | Initial release |

---

## License

MIT License — free to use, modify, and distribute. Attribution appreciated.