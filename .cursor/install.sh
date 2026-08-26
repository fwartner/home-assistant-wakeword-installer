#!/usr/bin/env bash
# Idempotent development bootstrap for the Wakeword Installer custom component.
# Creates an isolated virtualenv at .venv and installs the dev toolchain.
# Safe to re-run.
#
# Note: the component is imported via pytest's pythonpath=["."] (matching CI),
# so an editable `pip install -e .` is intentionally avoided. Editable installs
# inject a finder into the `custom_components` namespace that breaks Home
# Assistant's custom-component discovery when running a real HA instance.
set -euo pipefail

cd "$(dirname "$0")/.."

# The default base image ships Python 3.12 but may lack the venv module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  echo "Installing python3-venv system package..."
  sudo apt-get update -qq
  sudo apt-get install -y --no-install-recommends python3-venv
fi

# Create (or reuse) the project virtualenv.
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-dev.txt

echo "Development environment is ready. Activate it with: source .venv/bin/activate"
