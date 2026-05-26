import requests

BASE_URL = "http://localhost:8000"

def login(username, password):
    session = requests.Session()
    data = {"username": username, "password": password}
    resp = session.post(f"{BASE_URL}/login", data=data, allow_redirects=False)
    return session if resp.status_code == 303 else None

def test_upload():
    alice = login("alice", "alice123")
    if not alice:
        print("Login failed")
        return
    
    print("\n[Test 1] Upload valid JPEG...")
    with open("test.jpg", "wb") as f:
        f.write(b'\xff\xd8\xff\xdb')  # JPEG header
        f.write(b'\x00' * 1000)
    
    with open("test.jpg", "rb") as f:
        resp = alice.post(f"{BASE_URL}/files/upload", files={"file": ("test.jpg", f, "image/jpeg")})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ Valid JPEG uploaded")
    else:
        print(f"❌ Failed: {resp.text}")
    
    print("\n[Test 2] Upload fake JPEG (text file)...")
    with open("fake.jpg", "w") as f:
        f.write("This is not a real JPEG image")
    
    with open("fake.jpg", "rb") as f:
        resp = alice.post(f"{BASE_URL}/files/upload", files={"file": ("fake.jpg", f, "image/jpeg")})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 400:
        print("✅ Fake JPEG rejected (Magic bytes check works!)")
    else:
        print(f"❌ Failed: {resp.text}")

if __name__ == "__main__":
    test_upload()