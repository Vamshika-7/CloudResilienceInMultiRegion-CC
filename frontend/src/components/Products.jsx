import React from 'react';

export default function Products({ products, loading, onSelectProduct }) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
        Loading catalog products...
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
        No products available in the catalog.
      </div>
    );
  }

  return (
    <div>
      <h2 className="section-title">Product Catalog</h2>
      <p className="section-subtitle">
        Browse available items managed by the Product Service and PostgreSQL database.
      </p>

      <div className="grid-products">
        {products.map((product) => (
          <div key={product.id} className="card">
            <div className="card-header">
              <h3 className="card-title">{product.name}</h3>
              <span className="card-price">${parseFloat(product.price).toFixed(2)}</span>
            </div>

            <p className="card-desc">{product.description || "No description provided."}</p>

            <div className="card-footer">
              <div className="stock-tag">
                Stock:{" "}
                <span className={product.stock > 10 ? "stock-available" : "stock-low"}>
                  {product.stock} units
                </span>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => onSelectProduct(product)}
                disabled={product.stock <= 0}
              >
                {product.stock > 0 ? "Order Item" : "Out of Stock"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
