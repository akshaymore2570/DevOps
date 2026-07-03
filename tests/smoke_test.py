"""Smoke tests for pipeline"""
import requests
import sys

def test_smoke():
    print("🔥 Running smoke tests...")
    
    try:
        # Test health
        resp = requests.get('http://localhost:8080/health', timeout=5)
        assert resp.status_code == 200
        print("✅ Health check passed")
        
        # Test API
        resp = requests.get('http://localhost:8080/api/status', timeout=5)
        assert resp.status_code == 200
        print("✅ API check passed")
        
        print("✅ All smoke tests passed")
        return True
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if test_smoke() else 1)
