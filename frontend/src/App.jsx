import React, { useState, useEffect } from 'react';
import {
  fetchProducts,
  fetchOrders,
  fetchOrderById,
  createOrder,
  processPayment,
  fetchHealth
} from './api';
import Products from './components/Products';
import Orders from './components/Orders';
import PaymentModal from './components/PaymentModal';
import OrderDetailsModal from './components/OrderDetailsModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [activePaymentOrder, setActivePaymentOrder] = useState(null);
  const [detailedOrder, setDetailedOrder] = useState(null);
  const [healthData, setHealthData] = useState(null);

  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [alert, setAlert] = useState(null); // { type: 'success' | 'danger', message: string }

  const showAlert = (message, type = 'success') => {
    setAlert({ message, type });
    setTimeout(() => {
      setAlert(null);
    }, 6000);
  };

  const loadCatalog = async () => {
    setLoadingProducts(true);
    try {
      const data = await fetchProducts();
      setProducts(data);
    } catch (err) {
      console.error(err);
      showAlert(`Could not fetch products: ${err.message}`, 'danger');
    } finally {
      setLoadingProducts(false);
    }
  };

  const loadAllOrders = async () => {
    setLoadingOrders(true);
    try {
      const data = await fetchOrders();
      setOrders(data);
    } catch (err) {
      console.error(err);
      // Non-critical if no orders yet
    } finally {
      setLoadingOrders(false);
    }
  };

  const checkSystemHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealthData(data);
    } catch (err) {
      setHealthData({
        status: 'unreachable',
        error: err.message
      });
    }
  };

  useEffect(() => {
    loadCatalog();
    loadAllOrders();
    checkSystemHealth();
  }, []);

  const handleSelectProductForOrder = (product) => {
    setSelectedProduct(product);
    setActiveTab('orders');
  };

  const handleCreateOrder = async (orderPayload) => {
    try {
      const created = await createOrder(orderPayload);
      showAlert(`Order #${created.id} created successfully! Total: $${parseFloat(created.total_amount).toFixed(2)}`, 'success');
      await loadAllOrders();
      await loadCatalog(); // refresh stock
      setActivePaymentOrder(created); // prompt for payment right away!
    } catch (err) {
      showAlert(`Order creation failed: ${err.message}`, 'danger');
      throw err;
    }
  };

  const handleViewOrder = async (orderId) => {
    try {
      const order = await fetchOrderById(orderId);
      setDetailedOrder(order);
    } catch (err) {
      showAlert(err.message, 'danger');
    }
  };

  const handlePayPayment = async ({ orderId, amount, simulateFailure }) => {
    const res = await processPayment({ orderId, amount, simulateFailure });
    showAlert(
      `Payment #${res.id} for Order #${res.order_id} recorded: ${res.status}`,
      res.status === 'SUCCESS' ? 'success' : 'danger'
    );
    await loadAllOrders();
    return res;
  };

  return (
    <div>
      {/* Top Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="brand">
            <div className="brand-icon">📦</div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <h1>Cloud Commerce</h1>
                <span className="brand-tag">Milestone 1</span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Resilience Evaluation Research Testbed
              </p>
            </div>
          </div>

          <nav className="nav-tabs">
            <button
              className={`tab-btn ${activeTab === 'products' ? 'active' : ''}`}
              onClick={() => setActiveTab('products')}
            >
              Products
            </button>
            <button
              className={`tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('orders');
                loadAllOrders();
              }}
            >
              Orders ({orders.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'health' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('health');
                checkSystemHealth();
              }}
            >
              System Health
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container">
        {/* Banner Alert */}
        {alert && (
          <div className={`alert alert-${alert.type}`}>
            <span>{alert.message}</span>
            <button className="alert-close" onClick={() => setAlert(null)}>
              ×
            </button>
          </div>
        )}

        {/* View Switcher */}
        {activeTab === 'products' && (
          <Products
            products={products}
            loading={loadingProducts}
            onSelectProduct={handleSelectProductForOrder}
          />
        )}

        {activeTab === 'orders' && (
          <Orders
            products={products}
            orders={orders}
            selectedProduct={selectedProduct}
            onCreateOrder={handleCreateOrder}
            onInitiatePayment={(ord) => setActivePaymentOrder(ord)}
            onViewOrderDetails={handleViewOrder}
            loading={loadingOrders}
          />
        )}

        {activeTab === 'health' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 className="section-title">System Health & Microservice Observability</h2>
                <p className="section-subtitle">
                  Aggregated telemetry from API Gateway and downstream microservices.
                </p>
              </div>
              <button className="btn btn-outline" onClick={checkSystemHealth}>
                Refresh Health
              </button>
            </div>

            {healthData ? (
              <div>
                <div style={{
                  padding: '1.25rem',
                  background: 'white',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  marginBottom: '1.5rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600 }}>API Gateway Status:</span>
                    <span className={`badge ${healthData.status === 'healthy' ? 'badge-paid' : 'badge-failed'}`}>
                      {healthData.status}
                    </span>
                  </div>
                </div>

                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Downstream Microservices</h3>
                <div className="health-grid">
                  {healthData.downstream_services && Object.entries(healthData.downstream_services).map(([svc, status]) => (
                    <div key={svc} className="health-item">
                      <h4>{svc.replace('_', ' ').toUpperCase()}</h4>
                      <p className={status === 'healthy' ? 'health-status-healthy' : 'health-status-unhealthy'}>
                        {status}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>Checking service health status...</div>
            )}
          </div>
        )}
      </main>

      {/* Payment Modal */}
      {activePaymentOrder && (
        <PaymentModal
          order={activePaymentOrder}
          onClose={() => setActivePaymentOrder(null)}
          onPaySuccess={handlePayPayment}
        />
      )}

      {/* Order Details Modal */}
      {detailedOrder && (
        <OrderDetailsModal
          order={detailedOrder}
          onClose={() => setDetailedOrder(null)}
          onPay={(ord) => setActivePaymentOrder(ord)}
        />
      )}
    </div>
  );
}
