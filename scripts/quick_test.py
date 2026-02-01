#!/usr/bin/env python3
"""Quick test to verify everything is working."""

import os
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("QUICK SYSTEM TEST")
print("="*70)
print()

# Test 1: Environment variables
print("1. Checking environment variables...")
required = ["OPENAI_API_KEY", "WANDB_API_KEY", "WANDB_PROJECT"]
optional = ["WANDB_ENTITY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID"]

all_good = True
for var in required:
    if os.getenv(var):
        print(f"   ✅ {var}")
    else:
        print(f"   ❌ {var} - MISSING")
        all_good = False

for var in optional:
    if os.getenv(var):
        print(f"   ✅ {var}")
    else:
        print(f"   ⚠️  {var} - optional")

print()

# Test 2: Weave initialization
print("2. Testing Weave initialization...")
try:
    from rvla.weave_init import ensure_weave_init
    ensure_weave_init()
    import weave
    
    # Weave is initialized (that's what matters)
    print(f"   ✅ Weave initialized")
    print(f"   ✅ Ready to log traces")
except Exception as e:
    print(f"   ❌ Weave initialization failed: {e}")
    all_good = False

print()

# Test 3: Import core modules
print("3. Testing core module imports...")
try:
    from rvla.agent import run_agent
    from rvla.memory import workspace_from_env
    from rvla.web import WebDriver
    print("   ✅ All core modules imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    all_good = False

print()

# Test 4: Workspace
print("4. Testing workspace...")
try:
    workspace = workspace_from_env()
    print("   ✅ Workspace created")
except Exception as e:
    print(f"   ⚠️  Workspace creation warning: {e}")

print()

# Test 5: WebDriver (may fail if Browserbase not configured)
print("5. Testing WebDriver (optional - may fail if Browserbase not set)...")
try:
    driver = WebDriver()
    print("   ✅ WebDriver initialized")
    driver.close()
except Exception as e:
    print(f"   ⚠️  WebDriver not available: {e}")
    print("   (This is OK if you're not running browser automation)")

print()

# Summary
print("="*70)
if all_good:
    print("✅ SYSTEM READY!")
    print()
    print("You can now run:")
    print("  - python scripts/hackathon_demo.py")
    print("  - python scripts/showcase_weave_improvement.py")
    print("  - Start web UI: cd web && npm run dev")
else:
    print("⚠️  SOME ISSUES FOUND")
    print()
    print("Please set missing environment variables in .env file:")
    for var in required:
        if not os.getenv(var):
            print(f"  {var}=your_value_here")
print("="*70)
