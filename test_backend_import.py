#!/usr/bin/env python
"""Quick test to verify backend imports"""

try:
    from backend.main import app
    print("✓ Backend main imports successfully")
    
    routes = [r for r in app.routes if hasattr(r, 'path')]
    print(f"✓ Total routes registered: {len(routes)}")
    
    print("\nRegistered endpoints:")
    for route in routes:
        if hasattr(route, 'path'):
            print(f"  - {route.path}")
    
    print("\n✓ Backend validation complete - ready for antigravity!")
    
except Exception as e:
    print(f"✗ Backend import failed: {e}")
    import traceback
    traceback.print_exc()
