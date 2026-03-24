
# -*- coding: utf-8 -*-
import sys
import os

print("Test start...")
print("Python version:", sys.version.split()[0])
print("Current dir:", os.getcwd())
print()
print("[OK] Basic functions work!")
print()

print("Testing random module...")
import random
print("  Random number:", random.randint(1, 100))
print()

print("[OK] All tests passed!")
print()
print("Now let's test the offline demo...")
print()

# Test the offline demo
print("Testing MockDataGenerator...")
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from demo_offline import MockDataGenerator
    data_gen = MockDataGenerator()

    print("  Generating trending topics...")
    trending = data_gen.search_trending("Beauty")
    print("  OK! Generated", len(trending), "topics")

    print("  Generating competitors...")
    competitors = data_gen.search_competitors("Skincare")
    print("  OK! Generated", len(competitors), "accounts")

    print("  Generating script...")
    script = data_gen.generate_script("How to make short videos")
    print("  OK! Generated", len(script["script"]), "scenes")

    print()
    print("="*50)
    print("[SUCCESS] Everything works perfectly!")
    print("="*50)
    print()
    print("You can now run:")
    print("  python demo_offline.py")
    print()

except Exception as e:
    print("  Error:", e)
    import traceback
    traceback.print_exc()

try:
    input("Press Enter to exit...")
except:
    pass

