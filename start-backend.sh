#!/bin/sh
set -eu

# MUST match your package-manifest "id"
APPID="ctrlx-motor-ui"

# Where the proxy will look for your socket
RUNDIR="$SNAP_DATA/package-run/$APPID"
SOCK="$RUNDIR/web.sock"

# Ensure the run dir exists and is traversable by the proxy
# (x bit on dir allows entering; 0777 is safest across users)
install -d -m 0777 "$RUNDIR"

# Remove stale socket if present
[ -S "$SOCK" ] && rm -f "$SOCK"

# Make newly created socket world-connectable (uvicorn uses current umask)
umask 000

# Serve the built React app from the snap (mounted at $SNAP)
export STATIC_DIR="$SNAP/www"

# Launch FastAPI over UNIX domain socket
# --app-dir points uvicorn to where app.py lives inside the snap
exec uvicorn app:app --uds "$SOCK" --app-dir "$SNAP/backend" --log-level info
