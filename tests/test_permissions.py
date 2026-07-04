"""Access-control tests."""

POST = {"title": "A valid title", "content": "some content"}


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_unverified_cannot_create_post(client, make_user):
    token = await make_user("u@example.com", "unv", verified=False)
    resp = await client.post("/posts", json=POST, headers=_h(token))
    assert resp.status_code == 403


async def test_verified_can_create_post(client, make_user):
    token = await make_user("v@example.com", "ver", verified=True)
    resp = await client.post("/posts", json=POST, headers=_h(token))
    assert resp.status_code == 201


async def test_unverified_cannot_comment(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    unv = await make_user("u@example.com", "unv", verified=False)
    resp = await client.post(
        f"/posts/{post['id']}/comments", json={"content": "hi"}, headers=_h(unv)
    )
    assert resp.status_code == 403


async def test_non_owner_cannot_delete_post(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    other = await make_user("b@example.com", "bob", verified=True)
    resp = await client.delete(f"/posts/{post['id']}", headers=_h(other))
    assert resp.status_code == 403


async def test_owner_can_delete_post(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    resp = await client.delete(f"/posts/{post['id']}", headers=_h(owner))
    assert resp.status_code == 204
