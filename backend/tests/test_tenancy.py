async def test_user_cannot_access_others_item(client):
    user_a_data = {
        "name": "User A",
        "email": "userA@test.com",
        "password": "passA123",
    }

    user_a_item = {
        "title": "User A's secret item",
        "item_type": "task",
        "body": "This is private",
    }

    user_a_item_id , user_a_token = await user_signup_login_create_item(client , user_a_data, user_a_item)

    user_b_data = {
        "name": "User B",
        "email": "userB@test.com",
        "password": "passA123",
    }

    user_b_item = {
        "title": "User B's secret item",
        "item_type": "task",
        "body": "This is private",
    }

    user_b_item_id, user_b_token = await user_signup_login_create_item(client , user_b_data, user_b_item)

    # STEP 4: User B tries to access User A's item

    response = await client.get(
        f"/items/{user_a_item_id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )      
    
    
    # STEP 5: Assert 404
    assert response.status_code == 404

async def user_signup_login_create_item(client , user_data, user_item):

    await client.post("/auth/sign-up", json=user_data)
    
    login_user = await client.post("/auth/login", json={
        "email": user_data['email'],
        "password": user_data['password'],
    })

    token = login_user.json()["access_token"]
    
    # STEP 2: User item create
    # Header set  with token
    item_response = await client.post(
        "/items/",
        json=user_item,
        headers={"Authorization": f"Bearer {token}"}
    )

    item_id = item_response.json()["id"]    

    return item_id , token