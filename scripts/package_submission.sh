#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_path="${1:-$project_root/buildable-land-analysis-submission.zip}"
temporary_directory="$(mktemp -d)"
temporary_archive="$temporary_directory/submission.zip"
trap 'rm -rf "$temporary_directory"' EXIT

cd "$project_root"
zip -rq "$temporary_archive" . \
  -x '.git/*' \
  -x 'backend/venv/*' \
  -x 'backend/.env' \
  -x 'backend/.pytest_cache/*' \
  -x '*/__pycache__/*' \
  -x 'frontend/node_modules/*' \
  -x 'frontend/dist/*' \
  -x 'frontend/test-results/*' \
  -x 'frontend/playwright-report/*' \
  -x '*/.vite/*' \
  -x 'tmp/*' \
  -x '*.zip'

mv "$temporary_archive" "$output_path"

echo "Created $output_path"
