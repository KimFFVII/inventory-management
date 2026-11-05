"""
Tests for task and purchase order API endpoints.

Both resources live in module-level in-memory lists, so the autouse fixture
snapshots and restores them to keep tests independent of execution order.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def restore_state():
    """Restore in-memory tasks/purchase orders after each test."""
    tasks_before = list(main.tasks)
    pos_before = list(main.purchase_orders)
    yield
    main.tasks[:] = tasks_before
    main.purchase_orders[:] = pos_before


NEW_TASK = {"title": "Review reorder points", "priority": "high", "dueDate": "2025-10-10"}


def make_po(backlog_item_id, **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-01",
        "notes": "Rush",
    }
    payload.update(overrides)
    return payload


class TestTaskEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_returns_list(self, client):
        """Test getting tasks (no 404 on a fresh server)."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client):
        """Test creating a task."""
        response = client.post("/api/tasks", json=NEW_TASK)
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == NEW_TASK["title"]
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-10"
        assert task["status"] == "pending"
        # API ids start at 1000 to avoid colliding with client-side mock tasks
        assert task["id"] >= 1000

        assert any(t["id"] == task["id"] for t in client.get("/api/tasks").json())

    def test_create_task_ids_are_unique(self, client):
        """Test that consecutive tasks get different ids."""
        first = client.post("/api/tasks", json=NEW_TASK).json()
        second = client.post("/api/tasks", json=NEW_TASK).json()
        assert first["id"] != second["id"]

    def test_create_task_missing_fields(self, client):
        """Test that a task without a title or due date is rejected."""
        response = client.post("/api/tasks", json={"priority": "low"})
        assert response.status_code == 422

    def test_toggle_task(self, client):
        """Test toggling a task between pending and completed."""
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist."""
        response = client.patch("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task(self, client):
        """Test deleting a task."""
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert not any(t["id"] == task_id for t in client.get("/api/tasks").json())

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    @staticmethod
    def backlog_item_without_po(client):
        items = client.get("/api/backlog").json()
        item = next(i for i in items if not i["has_purchase_order"])
        return item["id"]

    def test_create_purchase_order(self, client):
        """Test creating a purchase order for a backlog item."""
        item_id = self.backlog_item_without_po(client)

        response = client.post("/api/purchase-orders", json=make_po(item_id))
        assert response.status_code == 201

        po = response.json()
        assert po["backlog_item_id"] == item_id
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 100
        assert po["unit_cost"] == 12.5
        assert po["status"] == "Pending"
        assert "id" in po
        assert "created_date" in po

    def test_created_po_marks_backlog_item(self, client):
        """Test that /api/backlog reflects the new purchase order."""
        item_id = self.backlog_item_without_po(client)
        client.post("/api/purchase-orders", json=make_po(item_id))

        items = client.get("/api/backlog").json()
        item = next(i for i in items if i["id"] == item_id)
        assert item["has_purchase_order"] is True

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching a purchase order by its backlog item id."""
        item_id = self.backlog_item_without_po(client)
        created = client.post("/api/purchase-orders", json=make_po(item_id)).json()

        response = client.get(f"/api/purchase-orders/{item_id}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_purchase_order_none_exists(self, client):
        """Test fetching a purchase order for an item that has none."""
        item_id = self.backlog_item_without_po(client)
        response = client.get(f"/api/purchase-orders/{item_id}")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test creating a purchase order for a nonexistent backlog item."""
        response = client.post("/api/purchase-orders", json=make_po("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_purchase_order(self, client):
        """Test that a backlog item can only have one purchase order."""
        item_id = self.backlog_item_without_po(client)
        assert client.post("/api/purchase-orders", json=make_po(item_id)).status_code == 201

        response = client.post("/api/purchase-orders", json=make_po(item_id))
        assert response.status_code == 409

    @pytest.mark.parametrize("overrides", [{"quantity": 0}, {"quantity": -5}, {"unit_cost": -1}])
    def test_create_purchase_order_invalid_numbers(self, client, overrides):
        """Test that non-positive quantity or negative cost is rejected."""
        item_id = self.backlog_item_without_po(client)
        response = client.post("/api/purchase-orders", json=make_po(item_id, **overrides))
        assert response.status_code == 400

    def test_create_purchase_order_missing_fields(self, client):
        """Test that missing required fields fail validation."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": "1"})
        assert response.status_code == 422
