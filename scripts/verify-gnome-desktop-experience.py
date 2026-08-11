#!/usr/bin/env python3
"""Fail when a GNOME image is only a session skeleton.

The input is one installed package name per line, as produced by
``rpm -qa --qf '%{NAME}\\n'`` or ``dpkg-query -W -f '${binary:Package}\\n'``.
Keeping this check package-manager agnostic lets the image build use the same
contract for RPM, DEB, and translated openSUSE package names.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable


REQUIRED_GNOME_PACKAGES = frozenset(
    {
        "gnome-keyring",
        "gnome-session",
        "gnome-shell",
        "gvfs",
        "mutter",
        "nautilus",
        "xdg-desktop-portal-gnome",
    }
)

# Ubuntu and Debian call the GNOME display manager gdm3; Fedora, EL and
# openSUSE call the same component gdm. Keep the contract about the desktop
# component rather than forcing every target through RPM naming.
REQUIRED_GNOME_PACKAGE_GROUPS = {
    "display-manager": frozenset({"gdm", "gdm3"}),
    **{package: frozenset({package}) for package in REQUIRED_GNOME_PACKAGES},
}


def missing_packages(
    installed: Iterable[str],
    required: Iterable[str] = REQUIRED_GNOME_PACKAGES,
) -> list[str]:
    installed_names = {line.strip().split()[0] for line in installed if line.strip()}
    groups = dict(REQUIRED_GNOME_PACKAGE_GROUPS)
    # Preserve the helper's useful custom-subset behavior for tests and other
    # callers while applying aliases to the default complete contract.
    if required != REQUIRED_GNOME_PACKAGES:
        groups = {name: frozenset({name}) for name in required}
    return sorted(name for name, aliases in groups.items() if not aliases & installed_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_list", help="file containing one installed package name per line")
    args = parser.parse_args()

    with open(args.package_list, encoding="utf-8") as package_list:
        missing = missing_packages(package_list)
    if missing:
        print("GNOME desktop contract failed; missing packages:", file=sys.stderr)
        for package in missing:
            print(f"  {package}", file=sys.stderr)
        return 1
    print("GNOME desktop contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
