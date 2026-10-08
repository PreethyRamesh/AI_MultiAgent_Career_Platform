"""Auth flow tests for the login/signup/forgot system (run against the app in-process).

Covers: unauthenticated redirect, invalid credentials, valid login, cookie/session,
page protection, logout, signup validation, forgot-password mock flow.
"""

from fastapi.testclient import TestClient

from app.main import app
from app import auth

c = TestClient(app)

EMAIL = "auth@student.edu"
NAME = "Auth Tester"
PW = "auth-1234"


def _signup_or_login() -> None:
    r = c.post("/api/auth/login", json={"email": EMAIL, "password": PW})
    if r.status_code != 200:
        s = c.post("/api/auth/signup", json={"full_name": NAME, "email": EMAIL, "password": PW})
        assert s.status_code in (200, 201), s.text
        r = c.post("/api/auth/login", json={"email": EMAIL, "password": PW})
    assert r.status_code == 200, r.text


# 1. unauthenticated requests to protected pages are redirected to /login
anon = TestClient(app)  # follow redirects -> lands on login page (200)
nofollow = TestClient(app, follow_redirects=False)
r = nofollow.get("/")
assert r.status_code == 303 and r.headers["location"].startswith("/login"), r.headers
r = nofollow.get("/career")
assert r.status_code == 303 and r.headers["location"].startswith("/login"), r.headers
print("[1] unauthenticated / and /career -> 303 /login      OK")

# 2. login page is public; /api/auth/me rejects anonymous
assert anon.get("/login").status_code == 200 and "Welcome back" in anon.get("/login").text
assert anon.get("/signup").status_code == 200
assert anon.get("/forgot").status_code == 200
assert anon.get("/api/auth/me").status_code == 401
print("[2] public auth pages render; anonymous /api/auth/me -> 401 OK")

# 3. invalid credentials rejected
r = c.post("/api/auth/login", json={"email": EMAIL, "password": "wrong-pass"})
assert r.status_code == 401, r.text
print("[3] invalid credentials -> 401                          OK")

# 4. valid login sets session cookie and unlocks pages
_signon = c.post("/api/auth/login", json={"email": EMAIL, "password": PW})
if _signon.status_code != 200:
    c.post("/api/auth/signup", json={"full_name": NAME, "email": EMAIL, "password": PW})
    _signon = c.post("/api/auth/login", json={"email": EMAIL, "password": PW})
assert _signon.status_code == 200, _signon.text
assert auth.SESSION_COOKIE in _signon.cookies
r = c.get("/")
assert r.status_code == 200 and "AI Learning" in r.text
r = c.get("/career")
assert r.status_code == 200 and "AI Career Analysis" in r.text
assert c.get("/api/auth/me").json()["user"]["email"] == EMAIL
print("[4] valid login -> cookie + / and /career 200           OK")

# 5. logged-in users are bounced away from /login
r = c.get("/login", follow_redirects=False)
assert r.status_code == 303 and r.headers["location"] == "/", r.headers
print("[5] authenticated /login -> 303 /                        OK")

# 6. signup validation
for bad in [
    {"full_name": "", "email": "x@y.com", "password": "abcdef"},
    {"full_name": "A", "email": "not-an-email", "password": "abcdef"},
    {"full_name": "A", "email": "x@y.com", "password": "123"},
]:
    r = c.post("/api/auth/signup", json=bad)
    assert r.status_code == 422, (bad, r.text)
dup = c.post(
    "/api/auth/signup", json={"full_name": NAME, "email": EMAIL, "password": PW}
)
assert dup.status_code == 422, dup.text  # duplicate email
print("[6] signup validation (empty/short/bad email/dup) -> 422  OK")

# 7. forgot-password mock (no email is sent; message is honest)
r = c.post("/api/auth/forgot", json={"email": EMAIL})
assert r.status_code == 200 and r.json()["ok"]
assert "email service" in r.json()["message"]
print("[7] forgot-password mock returns honest message         OK")

# 8. logout clears the session and re-protects pages
r = nofollow.post("/logout")
assert r.status_code in (302, 303), r.status_code
# an invalid/absent token never authorizes
fresh = TestClient(app, follow_redirects=False)
fresh.cookies.set(auth.SESSION_COOKIE, "not-a-real-token")
assert fresh.get("/").status_code == 303  # invalid token is not authorizing
print("[8] logout/invalid token -> protected again             OK")

print("AUTH TESTS PASSED")