#!/usr/bin/env bash
# Run with: bash start.sh

set -e
cd "$(dirname "$0")"

echo
echo "  YouTube auto-clipper"
echo

# Check deps
if ! node check-deps.js; then
    echo
    echo "  Install the missing dependencies above, then re-run this script."
    exit 1
fi

echo
node clip.js
