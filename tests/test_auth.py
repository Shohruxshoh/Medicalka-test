"""Authentication tests (registration, login, protected endpoints)."""


def _user(email: str, username: str) -> dict:
    return {
        "email": email,
        "username": username,
        "full_name": "Test User",
        "password": "password123",
    }


async def test_register_success(client):
    resp = await client.post("/auth/register", json=_user("a@example.com", "alice"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "a@example.com"
    assert data["is_verified"] is False
    assert "password" not in data
    assert "password_hash" not in data


async def test_register_duplicate_email(client):
    await client.post("/auth/register", json=_user("bob@example.com", "bob"))
    # Same email, different username.
    resp = await client.post("/auth/register", json=_user("bob@example.com", "bob2"))
    assert resp.status_code == 409


async def test_register_duplicate_username(client):
    await client.post("/auth/register", json=_user("carol@example.com", "carol"))
    # Same username, different email.
    resp = await client.post(
        "/auth/register", json=_user("carol2@example.com", "carol")
    )
    assert resp.status_code == 409


async def test_register_invalid_username(client):
    resp = await client.post("/auth/register", json=_user("x@example.com", "ab"))
    assert resp.status_code == 422  # username too short


async def test_login_success(client):
    await client.post("/auth/register", json=_user("dave@example.com", "dave"))
    resp = await client.post(
        "/auth/login",
        data={"username": "dave@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password(client):
    await client.post("/auth/register", json=_user("erin@example.com", "erin"))
    resp = await client.post(
        "/auth/login",
        data={"username": "erin@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_protected_endpoint_with_valid_token(client):
    await client.post("/auth/register", json=_user("frank@example.com", "frank"))
    login = await client.post(
        "/auth/login",
        data={"username": "frank@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "frank"


async def test_protected_endpoint_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_protected_endpoint_invalid_token(client):
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not.a.valid.token"}
    )
    assert resp.status_code == 401
