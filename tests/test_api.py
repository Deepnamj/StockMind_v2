
from fastapi.testclient import TestClient
from src.hitl.api import app


def main():

    # TestClient starts the FastAPI lifespan automatically.
    with TestClient(app) as client:

        print("\n========== 1. HEALTH CHECK ==========")

        response = client.get("/health")
        print(response.status_code, response.json())
        assert response.status_code == 200

        print("\n========== 2. FRONTEND ==========")

        response = client.get("/")
        print("Status:", response.status_code)
        print("HTML received:", "html" in response.text.lower())
        assert response.status_code == 200

        print("\n========== 3. COMPANY SEARCH ==========")

        response = client.get("/api/search", params={"q": "Apple"})
        print("Status:", response.status_code)
        print(response.json())
        assert response.status_code == 200

        print("\n========== 4. COMPANY OVERVIEW ==========")

        response = client.get("/api/company/AAPL")
        print("Status:", response.status_code)
        print(response.json())
        assert response.status_code == 200

        print("\n========== 5. LANGGRAPH CHAT ==========")

        response = client.post(
            "/api/chat",
            json={
                "message": "What is Apple's stock price? Use the stock tools.",
            }
        )

        print("Status:", response.status_code)
        chat_result = response.json()
        print(chat_result)

        assert response.status_code == 200
        assert chat_result["status"] == "completed"

        print("\n========== 6. APPROVAL WORKFLOW ==========")

        # Start a simulated purchase request
        purchase_response = client.post(
            "/api/chat",
            json={
                "message": (
                    "Use the request_simulated_stock_purchase tool "
                    "to request 2 AAPL shares at an estimated price "
                    "of 100 USD. Do not use any other tool."
                )
            }
        )

        print("Purchase request:", purchase_response.json())

        assert purchase_response.status_code == 200

        purchase_result = purchase_response.json()

        assert purchase_result["status"] == "approval_required"

        thread_id = purchase_result["thread_id"]

        # Approve the simulated purchase
        approval_response = client.post(
            "/api/approve",
            json={
                "thread_id": thread_id,
                "decision": "approve"
            }
        )

        print("\nApproval result:")
        print(approval_response.json())

        assert approval_response.status_code == 200
        assert approval_response.json()["status"] == "completed"

        print("\n========== 7. REJECTION WORKFLOW ==========")

        # Create another independent purchase request
        reject_request = client.post(
            "/api/chat",
            json={
                "message": (
                    "Use the request_simulated_stock_purchase tool "
                    "to request 2 AAPL shares at an estimated price "
                    "of 100 USD. Do not use any other tool."
                )
            }
        )

        assert reject_request.status_code == 200

        reject_result = reject_request.json()
        assert reject_result["status"] == "approval_required"

        # Reject the simulated purchase
        rejection_response = client.post(
            "/api/approve",
            json={
                "thread_id": reject_result["thread_id"],
                "decision": "reject"
            }
        )

        print("\nRejection result:")
        print(rejection_response.json())

        assert rejection_response.status_code == 200
        assert rejection_response.json()["status"] == "completed"

        print("\n========== ALL API TESTS PASSED ==========")


if __name__ == "__main__":
    main()
