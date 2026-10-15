#!/bin/sh
set -eu
root="${TANGLED_DATA_DIR:-./backend/data}"
destination="${1:-./backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$destination"
tar -czf "$destination/tangled-$timestamp.tar.gz" -C "$root" tangled.db chroma uploads
echo "Created $destination/tangled-$timestamp.tar.gz"
