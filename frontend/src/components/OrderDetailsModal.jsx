import React from 'react';

export default function OrderDetailsModal({ order, onClose, onPay }) {
  if (!order) return null;

  const statusClass =
    order.status === "PAID"
      ? "badge-paid"
      : order.status === "FAILED"
      ? "badge-failed"
      : "badge-pending";

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem'
    }}>
      <div className="card" style={{ maxWidth: '500px', width: '100%', padding: '1.75rem', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'transparent',
            border: 'none',
            fontSize: '1.25rem',
            cursor: 'pointer',
            color: 'var(--text-muted)'
          }}
        >
          ✕
        </button>

        <h3 className="section-title" style={{ fontSize: '1.3rem', marginBottom: '0.25rem' }}>
          Order Details #{order.id}
        </h3>
        <p className="section-subtitle" style={{ marginBottom: '1.25rem' }}>
          Retrieved from Order Service via API Gateway.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span className={`badge ${statusClass}`}>{order.status}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Customer ID:</span>
            <strong>{order.user_id}</strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Product ID:</span>
            <span>Product #{order.product_id}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Quantity:</span>
            <span>{order.quantity} units</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Total Amount:</span>
            <strong style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>
              ${parseFloat(order.total_amount).toFixed(2)}
            </strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Created At:</span>
            <span>{order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={onClose}>
            Close
          </button>
          {order.status === "PENDING" && (
            <button
              className="btn btn-success"
              onClick={() => {
                onClose();
                onPay(order);
              }}
            >
              Proceed to Payment
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
