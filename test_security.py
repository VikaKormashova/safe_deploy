import requests

BASE_URL = "http://localhost:8000"

def login_and_get_session(username, password):
    session = requests.Session()
    login_data = {"username": username, "password": password}
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    if response.status_code != 303:
        print(f"Login failed for {username}: status {response.status_code}")
        return None
    return session

def test_security():
    print("\n" + "="*60)
    print("Running Security Tests for HW8")
    print("="*60)

    alice = login_and_get_session("alice", "alice123")
    if not alice:
        print("❌ FAIL: Cannot login as alice")
        return

    print("\n[Test 1] Alice GET /files/1 (should be 200):")
    resp = alice.get(f"{BASE_URL}/files/1")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 200 else '❌ FAIL'}")

    print("\n[Test 2] Alice GET /files/2 (Bob's file, should be 404):")
    resp = alice.get(f"{BASE_URL}/files/2")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 404 else '❌ FAIL'}")

    bob = login_and_get_session("bob", "bob123")
    if not bob:
        print("❌ FAIL: Cannot login as bob")
        return

    print("\n[Test 3] Bob DELETE /files/2 (his own file, should be 200):")
    resp = bob.delete(f"{BASE_URL}/files/2")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 200 else '❌ FAIL'}")

    print("\n[Test 4] Alice GET /files/2 (check if deleted, should be 404):")
    resp = alice.get(f"{BASE_URL}/files/2")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 404 else '❌ FAIL'}")

    admin = login_and_get_session("admin", "admin123")
    if not admin:
        print("❌ FAIL: Cannot login as admin")
        return

    print("\n[Test 5] Admin GET /files/1 (any file, should be 200):")
    resp = admin.get(f"{BASE_URL}/files/1")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 200 else '❌ FAIL'}")

    print("\n[Test 6] Admin DELETE /files/1 (any file, should be 200):")
    resp = admin.delete(f"{BASE_URL}/files/1")
    print(f"Status: {resp.status_code} -> {'✅ PASS' if resp.status_code == 200 else '❌ FAIL'}")

    print("\n[Test 7] Alice GET /files/my (list her files):")
    resp = alice.get(f"{BASE_URL}/files/my")
    if resp.status_code == 200:
        files = resp.json().get("files", [])
        print(f"Status: 200 -> ✅ PASS, Alice has {len(files)} files")
    else:
        print(f"Status: {resp.status_code} -> ❌ FAIL")

    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_security()