# Debian and Ubuntu packaging

DEB packages are built from maintained `debian/` directories and published as
signed APT repositories under the `apt/ubuntu/` and `apt/debian/` R2 namespaces
declared in `manifests/package-factory.yaml`.

Do not add a PPA to a TunaOS image. Import the source/package metadata here,
record its provenance in `packages/<name>/source.yaml`, and rebuild it in CI.

## Owned Ubuntu Orca source package

`packages/orca/package.yaml` selects the existing Ubuntu 26.04 (`resolute`)
Tideforge target on both `amd64` and `arm64`. The factory planner discovers
owned recipes automatically; no parallel build list or publication default is
needed. Adding this recipe does not publish it.

This recipe uses `outputs.deb.native_source`, not the generated Debian
packaging renderer. Its source closure is the primary Ubuntu archive's exact
`50.3-0ubuntu0.1` signed `.dsc`, orig tarball and Debian tarball, each locked by
SHA-256. `packages/orca/source.yaml` records the hashes and downstream version
`50.3-0ubuntu0.1+tuna1`. Assembly checks the descriptor's identity, source
filenames, sizes and SHA-256 values against those locked archives. This is
checksum provenance, not a claim that the archive signature was verified.

The complete Ubuntu `debian/` directory remains authoritative: `control`,
`rules`, copyright, install files, wrapper, maintainer behavior and the existing
`unity-a11y.patch` are not regenerated. Assembly only appends the maintained
Tuna patch to quilt's series and prepends a downstream changelog entry. The
renderer rejects an invalid native-source mode before assembly can replace
packaging. Ordinary generated recipes retain their existing behavior.

### Assembly and native build

Run from the repository root. Assembly requires Python 3.12 or newer, PyYAML,
network access to the checksum-locked primary archive (or the existing source
cache), and an empty output directory. The following are commands for the
build owner, **not evidence that a build or installation has passed**:

```bash
work="$PWD/.factory/orca-native/deb"
mkdir -p "$work"
python3 scripts/tideforge.py render packages/orca/package.yaml \
  --target ubuntu --output "$work/rendered"
python3 scripts/assemble-deb-source-tree.py packages/orca/package.yaml "$work" ubuntu
docker run --rm -v "$work:/work" ubuntu:26.04 bash -lc '
  set -euo pipefail
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends build-essential ca-certificates
  cd "$(cat /work/source-dir)"
  apt-get build-dep -y --no-install-recommends "$PWD"
  dpkg-buildpackage -us -uc -S -sa
  dpkg-buildpackage -us -uc -b
'
```

Use the target's native architecture, not a foreign Python runtime or a copied
site-packages tree. Enable Ubuntu's native `universe` component if the build
image does not already enable it; do not import a PPA or another distribution's
packages to satisfy dependencies. `apt-get build-dep` must consume the
preserved Ubuntu `debian/control`, including its versioned AT-SPI requirements.
Do not bypass dependency checks with `-d`. The complete source build and binary
build use the native `dpkg-dev`/debhelper/Meson toolchain. Their `.dsc`, orig,
Debian tarball, `.changes`, `.buildinfo` and real `.deb` artifacts belong in the
build receipt, together with assembly's `source/original-source/` provenance.
An assembly-only tree or a source listing is not a compiled package.

For the existing isolated owned-recipe build selection, the planner IDs are
`tideforge-orca-ubuntu-amd64` and `tideforge-orca-ubuntu-arm64`; the build owner
uses the normal factory cell runner and clean-install verification. Do not
change the publisher's default wave or production repositories to test this.

For `native_source` recipes the cell runner builds the changed source with
`-S -sa` before its normal `-b` binary build, without skipping native checks.
It retains the complete changed source closure, source and binary `.changes`
and `.buildinfo`, and the locked original closure under `artifacts/source/`,
alongside the real DEB at the artifact root. Generated recipes keep their
existing binary-only build behavior.

### Installed package and runtime proof

Install only in a disposable native Ubuntu 26.04 guest/container, resolving
dependencies through its native APT sources:

```bash
apt-get update
apt-get install -y ./orca_50.3-0ubuntu0.1+tuna1_all.deb
dpkg-query -W -f='${Package} ${Version} ${Architecture}\n' orca
dpkg-query -S /usr/lib/python3/dist-packages/orca/scripts/apps/tuna-shell-gtk/script.py
```

The package manager must own the installed module. Do not overlay files,
set `PYTHONPATH`, monkeypatch the running Orca, or change user preferences to
make the proof pass. The recipe smoke check establishes package version and
module ownership only; it does not establish spoken feedback.

The maintained patch installs `tuna-shell-gtk/__init__.py` and
`tuna-shell-gtk/script.py` through upstream's `python3.install_sources`; it
does not install a flat `tuna-shell-gtk.py`. Ubuntu's exact 50.3 packaging
places existing app scripts under `usr/lib/python3/dist-packages/orca/scripts/apps/`
(the primary archive's `orca_50.3-0ubuntu0.1_all.deb` contains
`Thunderbird/script.py` at that prefix), which is the prefix used by the
ownership checks above.

Password speech qualification additionally requires the real native
`tuna-shell-gtk` app identity, its GTK password entry and AT-SPI event stream,
a session accessibility bus, the installed native Orca, Speech Dispatcher and
a working speech output/capture path. Prove committed insert/delete/reinsert
and paste counts without recording secret text or raw keys. Preserve the
first failure and any missing identity; neither a headless import nor a
synthetic shell announcement qualifies the native runtime path.

Before a version bump or retirement, compare the target-native source's
password event handling with this maintained patch and repeat the native
runtime proof. A newer Ubuntu version number is not by itself evidence that
this behavioral gap has closed. Retire the owned patch when the native source
actually supplies the correction, rather than retaining a runtime shim or
forcing an unrelated backport.
