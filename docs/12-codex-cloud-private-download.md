# Private Codex Cloud download setup (retained from PR #8)

PR #8 setup guidance is retained here; equivalent CLI and mock-only tests are supplied by PR #9. Exact environment UI labels may change; verify the variable reaches the task process without printing its value. For successful sample validation and consistent absolute paths see [T1.1 steps](11-squashfs-private-validation.md).

The owner has independently downloaded a candidate firmware from OM SYSTEM with `tools/ep7_firmware_fetch.py`. The script supports a **private, non-interactive** option for Codex Cloud.

## Personal Cloud setup

1. In **Settings → Codex Cloud → Environments**, edit the `ep7-film-hack` environment (private / Only me). Under **Environment variables → Manage**, add the `EP7_SERIAL` value from your camera as an environment variable, or supply it through Personal vault for only this environment. Do **not** enter the value in chat, Git, Issues or CI. **This value can be read by task processes/agent; it is not hidden from Codex.** Remove it after download is complete.
2. Enable task internet access, restricted to `fw01.om-digitalsolutions.net` (vendor XML POST) and `dl01.om-digitalsolutions.net` (firmware GET). If the vendor response redirects to a different OM-owned host, review and explicitly allow just that domain. POST must be permitted to the official request host.
3. From the private Cloud task, run:

```bash
set +x
python3 tools/ep7_firmware_fetch.py --serial-env EP7_SERIAL --output-dir /tmp/ep7-firmware
```

4. Verify size **111017984** and SHA-256 **9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb** against the owner's previously recorded candidate. A changed result requires **stop and explicit investigation**, not pretending the same image.
5. The downloaded OEM bytes and any extracted image stay in the **private task filesystem under `/tmp`**, outside the checked-out Git repository; never push, upload as an artifact, print the XML request, or attach to a public PR. No camera is connected, modified or flashed.

`--serial-env` uses a regular environment variable, **not** a guarantee of secret isolation. Newer Codex Cloud Network Secrets use proxy substitution and are not interchangeable with a raw environment variable read by this script. Set only the needed domain permissions, do not run `env`, `set -x`, or echo the request XML. Delete the setting once the one-time download is complete.

## Alternative

If the OEM host cannot be reached from Cloud or rejects its requests, stop. Use a private encrypted object-storage bucket and a short-lived, read-only signed URL **only if the firmware's applicable terms permit** storing a private copy there; do not use a public release or Git LFS in this public repository.
