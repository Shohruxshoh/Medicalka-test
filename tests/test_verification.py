"""Email-verification flow tests."""


async def test_verification_flow(client):
    await client.post(
        "/auth/register",
        json={
            "email": "v@example.com",
            "username": "vuser",
            "full_name": "V User",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/auth/request-verification", json={"email": "v@example.com"}
    )
    assert resp.status_code == 200
    token = resp.json()["verification_token"]
    assert token

    verify = await client.get(f"/auth/verify-email?token={token}")
    assert verify.status_code == 200
    assert verify.json()["is_verified"] is True


async def test_verify_invalid_token(client):
    resp = await client.get("/auth/verify-email?token=not-a-real-token")
    assert resp.status_code == 400
