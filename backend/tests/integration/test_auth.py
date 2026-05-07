async def test_register_success(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "username": "NewUser",
        "password": "pass1234",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["username"] == "NewUser"
    assert "hashed_password" not in data["user"]


async def test_register_with_telegram(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "tg@test.com",
        "username": "TGUser",
        "password": "pass1234",
        "telegram_username": "tg_handle",
    })
    assert r.status_code == 200
    assert r.json()["user"]["telegram_username"] == "tg_handle"


async def test_register_duplicate_email(client, test_user):
    r = await client.post("/api/v1/auth/register", json={
        "email": "teacher@test.com",  # same as test_user fixture
        "username": "AnotherUser",
        "password": "pass1234",
    })
    assert r.status_code == 400


async def test_login_success(client, test_user):
    r = await client.post("/api/v1/auth/login", json={
        "email": "teacher@test.com",
        "password": "secret123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "teacher@test.com"


async def test_login_wrong_password(client, test_user):
    r = await client.post("/api/v1/auth/login", json={
        "email": "teacher@test.com",
        "password": "wrongpass",
    })
    assert r.status_code == 401


async def test_login_unknown_email(client):
    r = await client.post("/api/v1/auth/login", json={
        "email": "ghost@test.com",
        "password": "pass1234",
    })
    assert r.status_code == 401


async def test_get_me_success(client, auth_headers, test_user):
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


async def test_get_me_no_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


async def test_get_me_invalid_token(client):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code == 401


async def test_register_returns_valid_token(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "tokencheck@test.com",
        "username": "TokenUser",
        "password": "pass1234",
    })
    token = r.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "tokencheck@test.com"


async def test_login_returns_valid_token(client, test_user):
    r = await client.post("/api/v1/auth/login", json={
        "email": "teacher@test.com",
        "password": "secret123",
    })
    token = r.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["id"] == test_user.id
