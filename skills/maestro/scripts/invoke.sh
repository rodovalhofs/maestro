#!/usr/bin/env sh
# Maestro script wrapper — resolves bundled Python scripts
set -e

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  search) SCRIPT="search_skills.py" ;;
  route) SCRIPT="route_tasks.py" ;;
  manifest) SCRIPT="build_manifest.py" ;;
  *)
    echo "Usage: invoke.sh <search|route|manifest> [args...]" >&2
    echo "Prefer: npx maestro-skills search \"query\" --json" >&2
    exit 1
    ;;
esac

DIR="$(CDPATH= cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/$SCRIPT" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$DIR/$SCRIPT" "$@"
else
  echo "Python not found. Use: npx maestro-skills search" >&2
  exit 1
fi
