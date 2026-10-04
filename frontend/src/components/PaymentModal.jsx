import React, { useState } from 'react';

export default function PaymentModal({ order, onClose, onPaySuccess }) {
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [paying, setPaying] = useState(false);
  const [paymentResult, setPaymentResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!order) return null;

  const handlePayment = async (e) => {
    e.preventDefault();
    setPaying(true);
    setErrorMsg(null);
    try {
      const res = await onPaySuccess({
        orderId: order.id,
        amount: order.total_amount,
        simulateFailure
      });
      setPaymentResult(res);
    } catch (err) {
      setErrorMsg(err.message || "Payment request failed");
    } finally {
      setPaying(false);
    }
  };

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
      <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '1.75rem', position: 'relative' }}>
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
          Process Payment
        </h3>
        <p className="section-subtitle" style={{ marginBottom: '1.25rem' }}>
          Simulates payment transaction with Payment Service via API Gateway.
        </p>

        {errorMsg && (
          <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
            {errorMsg}
          </div>
        )}

        {paymentResult ? (
          <div>
            <div
              className={`alert ${paymentResult.status === "SUCCESS" ? "alert-success" : "alert-danger"}`}
              style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}
            >
              <div style={{ fontWeight: 'bold', fontSize: '1.05rem' }}>
                Payment {paymentResult.status}!
              </div>
              <div>Transaction ID: #{paymentResult.id}</div>
              <div>Order ID: #{paymentResult.order_id}</div>
              <div>Amount: ${parseFloat(paymentResult.amount).toFixed(2)}</div>
              <div>Method: {paymentResult.payment_method}</div>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '1rem' }}
              onClick={onClose}
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handlePayment}>
            <div className="form-group">
              <label className="form-label">Order ID</label>
              <input
                type="text"
                className="form-control"
                value={`#${order.id}`}
                disabled
              />
            </div>

            <div className="form-group">
              <label className="form-label">Amount to Pay ($)</label>
              <input
                type="text"
                className="form-control"
                value={`$${parseFloat(order.total_amount).toFixed(2)}`}
                disabled
                style={{ fontWeight: 'bold', color: 'var(--primary)' }}
              />
            </div>

            <div style={{
              background: '#f8fafc',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.85rem',
              marginBottom: '1.25rem'
            }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                <input
                  type="checkbox"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                />
                <span><strong>Chaos Simulation:</strong> Simulate payment rejection / failure</span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-outline" onClick={onClose} disabled={paying}>
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-success"
                disabled={paying}
              >
                {paying ? "Processing..." : `Confirm Payment of $${parseFloat(order.total_amount).toFixed(2)}`}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
