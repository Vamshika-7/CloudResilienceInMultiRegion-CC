// API client for communicating exclusively with the API Gateway

const GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000/api";
const GATEWAY_BASE = GATEWAY_URL.replace(/\/api\/?$/, "");

export async function fetchHealth() {
  const res = await fetch(`${GATEWAY_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Gateway returned health check error: ${res.status}`);
  }
  return res.json();
}

export async function fetchProducts() {
  const res = await fetch(`${GATEWAY_URL}/products`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch products: ${res.status}`);
  }
  return res.json();
}

export async function fetchProductById(id) {
  const res = await fetch(`${GATEWAY_URL}/products/${id}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch product ${id}`);
  }
  return res.json();
}

export async function createOrder({ userId = "user_demo", productId, quantity }) {
  const res = await fetch(`${GATEWAY_URL}/orders`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: userId,
      product_id: parseInt(productId, 10),
      quantity: parseInt(quantity, 10)
    })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Failed to create order: ${res.status}`);
  }
  return data;
}

export async function fetchOrders() {
  const res = await fetch(`${GATEWAY_URL}/orders`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch orders`);
  }
  return res.json();
}

export async function fetchOrderById(id) {
  const res = await fetch(`${GATEWAY_URL}/orders/${id}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Order #${id} not found`);
  }
  return res.json();
}

export async function processPayment({ orderId, amount, simulateFailure = false }) {
  const res = await fetch(`${GATEWAY_URL}/payments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      order_id: parseInt(orderId, 10),
      amount: parseFloat(amount),
      simulate_failure: simulateFailure
    })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Payment failed with status ${res.status}`);
  }
  return data;
}
