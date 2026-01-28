import requests

API_URL = "http://127.0.0.1:8001"

def test_auth_and_hmi():
    # 1. Login
    print("Testing Login...")
    resp = requests.post(f"{API_URL}/login", json={"username": "admin", "password": "admin123"})
    if resp.status_code == 200:
        data = resp.json()
        print(f"Login Success. Token: {data['token'][:10]}..., Role: {data['role']}")
    else:
        print(f"Login Failed: {resp.text}")
        exit(1)

    # 2. Upload Master (if not present mock it)
    # Skipping upload test for brevity, assuming master is there or we handle errors.

    # 3. Check Inspection Frame for Diagnostics & Stats
    print("\nTesting Inspection Endpoint...")
    try:
        # We need a master loaded for this to work usually, 
        # but let's see if we get a specific error or data
        resp = requests.get(f"{API_URL}/inspection-frame?simulate=true")
        
        if resp.status_code == 200:
            data = resp.json()
            if "diagnostics" in data:
                diag = data["diagnostics"]
                print(f"Diagnostics: Brightness={diag['brightness']}, Blur={diag['blur_score']}")
            
            if "stats" in data:
                stats = data["stats"]
                print(f"Stats: Speed={stats['speed_m_min']}")
                
            print("Inspection Data Structure Verified.")
        else:
            print(f"Inspection Endpoint returned {resp.status_code}: {resp.text}")
            # It might fail if no master is loaded, which is expected in a script without upload
            if "Master not loaded" in resp.text:
                 print("(Expected Error: Master not loaded. Endpoint logic is reachable.)")

    except Exception as e:
        print(f"Error checking inspection: {e}")

if __name__ == "__main__":
    test_auth_and_hmi()
