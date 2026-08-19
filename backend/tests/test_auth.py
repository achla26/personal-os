
async def test_login_wrong_password(client):
    # Signup user
    await client.post("/auth/sign-up", json={
        "name": "Test",
        "email": "test@test.com",
        "password": "correctpass",
    })
    
    # Wrong password login
    response_wrong_pass = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "wrongpass",
    })
    
    # Unknown email login
    response_unknown = await client.post("/auth/login", json={
        "email": "unknown@test.com",
        "password": "anything",
    })
    
    # Assert both 401
    assert response_wrong_pass.status_code == 401
    assert response_unknown.status_code == 401
    
    # Assert both message same
    assert response_wrong_pass.json()["detail"] == response_unknown.json()["detail"]