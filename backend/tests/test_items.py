async def test_create_item(auth_client):
    # auth_client already logged 
    response = await auth_client.post(
        "/items/",
        json={
            "title": "Buy milk",
            "item_type": "task",
            "body": "2 liters",
        }
    )
    
    # Assert status
    assert response.status_code == 201
    
    # Assert response body
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["item_type"] == "task"
    assert data["body"] == "2 liters"
    assert "id" in data
    assert "created_at" in data

async def test_auth_required(client):
    # client (auth_client no!) - no token 
    response = await client.get("/items/")
    
    assert response.status_code == 401


async def test_mark_done(auth_client):
    # 1. Item create 
    create_response = await auth_client.post(
        "/items/",
        json={
            "title": "Test task",
            "item_type": "task",
            "body": "Complete this",
        }
    )
    item_id = create_response.json()["id"]
    
    # 2. PATCH done mark 
    patch_response = await auth_client.patch(
        f"/items/{item_id}",
        json={"status": "done"}
    )
    
    # 3. Assert
    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["status"] == "done"
    assert data["completed_at"] is not None  # filled
    assert data["next_nag_at"] is None       # cleared

