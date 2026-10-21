#!/usr/bin/env bash
# Load API keys from the private env file (never printed), then exec the given command.
set -euo pipefail
set -a; . "$HOME/.config/trustcurve/env"; set +a
exec "$@"
