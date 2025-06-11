# Blake2 Hash Algorithm Error Fix

## Problem
Error messages appearing during tests:
```
ERROR:root:code for hash blake2b was not found.
ERROR:root:code for hash blake2s was not found.
```

## Root Cause
Python 3.11.6 installed via pyenv lacks proper OpenSSL support for blake2b/blake2s algorithms.

## Solutions

### Option 1: Reinstall Python with proper OpenSSL (Recommended)
```bash
# Set OpenSSL flags before installing Python
export LDFLAGS="-L$(brew --prefix openssl@3)/lib"
export CPPFLAGS="-I$(brew --prefix openssl@3)/include"
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"

# Reinstall Python with OpenSSL support
pyenv install 3.11.10
pyenv local 3.11.10
```

### Option 2: Use conda instead of pyenv
```bash
# Install miniconda
brew install miniconda
conda create -n keapmcp python=3.11
conda activate keapmcp
pip install -r requirements.txt
```

### Option 3: Suppress warnings (Current Implementation)
- Added filterwarnings to pyproject.toml
- Added logging suppression in conftest.py
- Tests still pass despite the warnings

## Status
✅ Warnings suppressed in test configuration
✅ No functional impact on the application
⚠️ Consider upgrading Python installation for clean resolution

## Testing
The blake2 algorithms are not used by our codebase, so the errors don't affect functionality.