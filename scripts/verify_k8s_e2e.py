"""
End-to-end validation script for the Kubernetes (K3s) deployment.
Tests all operational endpoints through both the Frontend Ingress and API Gateway:
1. Direct Gateway Health check (/health on port 8000)
2. Frontend UI retrieval (/ on port 5173)
3. Frontend Ingress / Nginx reverse proxy health check (/health on port 5173)
4. Product catalog retrieval (/api/products on port 5173)
5. Order creation (/api/orders on port 5173)
6. Order lookup (/api/orders/{id} on port 5173)
7. Successful payment flow (/api/payments on port 5173)
8. Simulated payment failure flow (/api/payments on port 5173)
"""

import sys
import json
import urllib.request
import urllib.error

FRONTEND_URL = "http://localhost:5173"
GATEWAY_URL = "http://localhost:8000"

def request(url, method="GET", data=None):
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            status = resp.status
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return status, parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

def main():
    print("=" * 60)
    print("KUBERNETES END-TO-END DEPLOYMENT VERIFICATION")
    print("=" * 60)

    # 1. Gateway Direct Health Check
    print("\n1. Testing API Gateway direct health check (port 8000)...")
    status, body = request(f"{GATEWAY_URL}/health")
    assert status == 200, f"Gateway health failed: status={status}, body={body}"
    assert body.get("status") == "healthy", f"Gateway unhealthy: {body}"
    downstreams = body.get("downstream_services", {})
    assert downstreams.get("product_service") == "healthy", f"Product service unhealthy: {downstreams}"
    assert downstreams.get("order_service") == "healthy", f"Order service unhealthy: {downstreams}"
    assert downstreams.get("payment_service") == "healthy", f"Payment service unhealthy: {downstreams}"
    print("   [PASS] Gateway and all downstream services are healthy.")

    # 2. Frontend UI retrieval
    print("\n2. Testing Frontend UI retrieval via Traefik Ingress (port 5173)...")
    status, body = request(f"{FRONTEND_URL}/")
    assert status == 200, f"Frontend failed: status={status}, body={body}"
    assert "<title>E-Commerce Microservices - Resilience Research Lab</title>" in body, "Frontend HTML missing title"
    print("   [PASS] Frontend static bundle served successfully.")

    # 3. Frontend Ingress / Nginx Proxy Health Check
    print("\n3. Testing Health check through Frontend Ingress proxy (port 5173)...")
    status, body = request(f"{FRONTEND_URL}/health")
    assert status == 200, f"Frontend health proxy failed: status={status}, body={body}"
    assert body.get("status") == "healthy", f"Frontend proxy unhealthy: {body}"
    print("   [PASS] Frontend proxy correctly routes /health to Gateway.")

    # 4. Product Catalog Retrieval
    print("\n4. Testing Product catalog retrieval (/api/products)...")
    status, products = request(f"{FRONTEND_URL}/api/products")
    assert status == 200, f"Get products failed: status={status}, body={products}"
    assert isinstance(products, list) and len(products) >= 6, f"Expected at least 6 products, got: {len(products)}"
    first_prod = products[0]
    print(f"   [PASS] Retrieved {len(products)} products. First product: '{first_prod['name']}' (Stock: {first_prod['stock']})")

    # 5. Order Creation
    print("\n5. Testing Order creation (/api/orders)...")
    order_payload = {
        "user_id": "cust-k8s-001",
        "product_id": first_prod["id"],
        "quantity": 1
    }
    status, order = request(f"{FRONTEND_URL}/api/orders", method="POST", data=order_payload)
    assert status == 201, f"Order creation failed: status={status}, body={order}"
    order_id = order.get("id")
    assert order_id, f"Order missing id: {order}"
    assert order.get("status").upper() == "PENDING", f"Unexpected status: {order.get('status')}"
    print(f"   [PASS] Created order #{order_id} (Status: {order.get('status')}, Total: ${order.get('total_amount')})")

    # 6. Order Lookup
    print(f"\n6. Testing Order lookup (/api/orders/{order_id})...")
    status, fetched_order = request(f"{FRONTEND_URL}/api/orders/{order_id}")
    assert status == 200, f"Order lookup failed: status={status}, body={fetched_order}"
    assert fetched_order.get("id") == order_id, f"Order ID mismatch: {fetched_order}"
    assert fetched_order.get("product_id") == first_prod["id"]
    print(f"   [PASS] Order #{order_id} retrieved successfully.")

    # 7. Successful Payment Flow
    print(f"\n7. Testing successful payment for order #{order_id} (/api/payments)...")
    payment_payload = {
        "order_id": order_id,
        "amount": float(fetched_order.get("total_amount")),
        "simulate_failure": False
    }
    status, payment = request(f"{FRONTEND_URL}/api/payments", method="POST", data=payment_payload)
    assert status == 200, f"Payment failed: status={status}, body={payment}"
    assert payment.get("status").upper() == "SUCCESS", f"Payment not success: {payment}"
    print(f"   [PASS] Payment #{payment.get('id')} processed with status: {payment.get('status')}.")

    # Verify order status transitioned to PAID
    status, updated_order = request(f"{FRONTEND_URL}/api/orders/{order_id}")
    assert status == 200
    assert updated_order.get("status").upper() == "PAID", f"Order status should be 'PAID', got: {updated_order.get('status')}"
    print(f"   [PASS] Order #{order_id} status transitioned to 'PAID'.")

    # 8. Simulated Payment Failure Flow
    print("\n8. Testing simulated payment failure flow...")
    fail_order_payload = {
        "user_id": "cust-k8s-fail",
        "product_id": first_prod["id"],
        "quantity": 1
    }
    status, fail_order = request(f"{FRONTEND_URL}/api/orders", method="POST", data=fail_order_payload)
    assert status == 201
    fail_order_id = fail_order.get("id")

    fail_payment_payload = {
        "order_id": fail_order_id,
        "amount": float(fail_order.get("total_amount")),
        "simulate_failure": True
    }
    status, fail_payment = request(f"{FRONTEND_URL}/api/payments", method="POST", data=fail_payment_payload)
    assert status == 200, f"Expected 200 for simulated failure, got: status={status}, body={fail_payment}"
    assert fail_payment.get("status").upper() == "FAILED", f"Expected status FAILED, got: {fail_payment}"
    print(f"   [PASS] Simulated payment #{fail_payment.get('id')} recorded with status: {fail_payment.get('status')}.")

    status, order_after_fail = request(f"{FRONTEND_URL}/api/orders/{fail_order_id}")
    assert status == 200
    assert order_after_fail.get("status").upper() == "FAILED", f"Expected 'FAILED', got: {order_after_fail.get('status')}"
    print(f"   [PASS] Order #{fail_order_id} status transitioned to 'FAILED'.")

    print("\n" + "=" * 60)
    print("ALL END-TO-END TESTS PASSED ON KUBERNETES CLUSTER!")
    print("=" * 60)

if __name__ == "__main__":
    main()
