import React, { useState } from 'react';

export default function Orders({
  products,
  orders,
  selectedProduct,
  onCreateOrder,
  onInitiatePayment,
  onViewOrderDetails,
  loading
}) {
  const [selectedProductId, setSelectedProductId] = useState(
    selectedProduct ? selectedProduct.id : (products[0]?.id || '')
  );
  const [quantity, setQuantity] = useState(1);
  const [userId, setUserId] = useState("user_researcher");
  const [submitting, setSubmitting] = useState(false);
  const [lookupId, setLookupId] = useState('');

  const currentProduct = products.find((p) => p.id === parseInt(selectedProductId, 10));
  const estimatedTotal = currentProduct ? (parseFloat(currentProduct.price) * quantity).toFixed(2) : '0.00';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedProductId) return;
    setSubmitting(true);
    try {
      await onCreateOrder({
        userId,
        productId: selectedProductId,
        quantity
      });
      setQuantity(1);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLookup = (e) => {
    e.preventDefault();
    if (lookupId.trim()) {
      onViewOrderDetails(lookupId.trim());
    }
  };

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem', marginBottom: '2.5rem' }}>
        {/* Create Order Card */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 className="section-title" style={{ fontSize: '1.25rem' }}>Place New Order</h3>
          <p className="section-subtitle" style={{ marginBottom: '1rem' }}>
            Communicates through API Gateway to Order Service and Product Service.
          </p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Customer ID</label>
              <input
                type="text"
                className="form-control"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Select Product</label>
              <select
                className="form-control"
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                required
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} - ${parseFloat(p.price).toFixed(2)} ({p.stock} in stock)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Quantity</label>
              <input
                type="number"
                min="1"
                max={currentProduct?.stock || 99}
                className="form-control"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value || '1', 10))}
                required
              />
            </div>

            <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '6px', marginBottom: '1.25rem', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                <span>Unit Price:</span>
                <span>${currentProduct ? parseFloat(currentProduct.price).toFixed(2) : '0.00'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '1.05rem', marginTop: '0.25rem', color: 'var(--primary)' }}>
                <span>Estimated Total:</span>
                <span>${estimatedTotal}</span>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={submitting || !currentProduct || currentProduct.stock < quantity}
            >
              {submitting ? "Placing Order..." : "Create Order"}
            </button>
          </form>
        </div>

        {/* Order Lookup Card */}
        <div className="card" style={{ padding: '1.5rem', alignSelf: 'flex-start' }}>
          <h3 className="section-title" style={{ fontSize: '1.25rem' }}>Lookup Order by ID</h3>
          <p className="section-subtitle" style={{ marginBottom: '1rem' }}>
            Fetch specific order details from the Order Service via Gateway.
          </p>

          <form onSubmit={handleLookup} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="number"
              className="form-control"
              placeholder="e.g. 1"
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-outline" style={{ whiteSpace: 'nowrap' }}>
              View Details
            </button>
          </form>
        </div>
      </div>

      {/* Orders Table */}
      <h3 className="section-title">Recent Orders</h3>
      <p className="section-subtitle">Persistent order records stored in PostgreSQL.</p>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading orders...</div>
      ) : orders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', background: 'white', border: '1px solid var(--border)', borderRadius: '8px' }}>
          No orders created yet. Select a product above to place your first order.
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>User</th>
                <th>Product ID</th>
                <th>Qty</th>
                <th>Total</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const statusClass =
                  order.status === "PAID"
                    ? "badge-paid"
                    : order.status === "FAILED"
                    ? "badge-failed"
                    : "badge-pending";

                return (
                  <tr key={order.id}>
                    <td><strong>#{order.id}</strong></td>
                    <td>{order.user_id}</td>
                    <td>Product #{order.product_id}</td>
                    <td>{order.quantity}</td>
                    <td><strong>${parseFloat(order.total_amount).toFixed(2)}</strong></td>
                    <td>
                      <span className={`badge ${statusClass}`}>{order.status}</span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {order.created_at ? new Date(order.created_at).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                          onClick={() => onViewOrderDetails(order.id)}
                        >
                          View
                        </button>
                        {order.status === "PENDING" && (
                          <button
                            className="btn btn-success"
                            style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }}
                            onClick={() => onInitiatePayment(order)}
                          >
                            Pay
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
