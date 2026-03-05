#!/usr/bin/env python3
"""Quick verification script for Quant Trader backend"""

import sys
import os

print("=" * 60)
print("Quant Trader - Quick Verification")
print("=" * 60)

# Check directory structure
print("\n1. Checking directory structure...")
required_dirs = ['api', 'core', 'strategies']
for d in required_dirs:
    if os.path.isdir(d):
        print(f"   ✓ {d}/")
    else:
        print(f"   ✗ {d}/ - MISSING")
        sys.exit(1)

# Check required files
print("\n2. Checking required files...")
required_files = [
    'config.py', 'database.py', 'models.py', 'main.py',
    'requirements.txt',
    'api/__init__.py', 'api/strategies.py', 'api/backtest.py',
    'api/signals.py', 'api/notify.py',
    'core/__init__.py', 'core/data_fetcher.py', 'core/strategy_engine.py',
    'core/backtest_engine.py', 'core/notifier.py',
    'strategies/__init__.py', 'strategies/technical.py', 'strategies/multi_factor.py'
]
for f in required_files:
    if os.path.isfile(f):
        print(f"   ✓ {f}")
    else:
        print(f"   ✗ {f} - MISSING")
        sys.exit(1)

# Try importing modules
print("\n3. Testing module imports...")
sys.path.insert(0, '.')

try:
    import config
    print("   ✓ config.py imported")
except Exception as e:
    print(f"   ✗ config.py import failed: {e}")

try:
    import database
    print("   ✓ database.py imported")
except Exception as e:
    print(f"   ✗ database.py import failed: {e}")

try:
    import models
    print("   ✓ models.py imported")
except Exception as e:
    print(f"   ✗ models.py import failed: {e}")

try:
    from core import strategy_engine
    print("   ✓ core/strategy_engine.py imported")
except Exception as e:
    print(f"   ✗ core/strategy_engine.py import failed: {e}")

try:
    from core import backtest_engine
    print("   ✓ core/backtest_engine.py imported")
except Exception as e:
    print(f"   ✗ core/backtest_engine.py import failed: {e}")

try:
    from strategies import technical, multi_factor
    print("   ✓ strategies imported")
except Exception as e:
    print(f"   ✗ strategies import failed: {e}")

print("\n" + "=" * 60)
print("Verification complete! All files are in place.")
print("=" * 60)
print("\nNext steps:")
print("  1. cd backend")
print("  2. python -m venv venv")
print("  3. source venv/bin/activate")
print("  4. pip install -r requirements.txt")
print("  5. cp .env.example .env  # Edit with your credentials")
print("  6. uvicorn main:app --reload --port 8000")
print("\nThen in another terminal:")
print("  1. cd frontend")
print("  2. npm install")
print("  3. npm run dev")
print()
