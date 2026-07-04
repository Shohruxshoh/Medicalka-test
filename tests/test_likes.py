"""Like-rule tests."""

POST = {"title": "A valid title", "content": "some content"}


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_cannot_like_own_post(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    resp = await client.post(f"/posts/{post['id']}/like", headers=_h(owner))
    assert resp.status_code == 400


async def test_cannot_like_twice(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    liker = await make_user("l@example.com", "liker", verified=True)

    first = await client.post(f"/posts/{post['id']}/like", headers=_h(liker))
    assert first.status_code == 200
    assert first.json()["likes_count"] == 1

    second = await client.post(f"/posts/{post['id']}/like", headers=_h(liker))
    assert second.status_code == 409


async def test_unverified_can_like(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    unv = await make_user("u@example.com", "unv", verified=False)
    resp = await client.post(f"/posts/{post['id']}/like", headers=_h(unv))
    assert resp.status_code == 200
    assert resp.json()["likes_count"] == 1


async def test_unlike(client, make_user):
    owner = await make_user("o@example.com", "owner", verified=True)
    post = (await client.post("/posts", json=POST, headers=_h(owner))).json()
    liker = await make_user("l@example.com", "liker", verified=True)
    await client.post(f"/posts/{post['id']}/like", headers=_h(liker))

    resp = await client.delete(f"/posts/{post['id']}/like", headers=_h(liker))
    assert resp.status_code == 200
    assert resp.json()["liked"] is False
    assert resp.json()["likes_count"] == 0
