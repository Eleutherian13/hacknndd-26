import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Package, Clock, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

const OrdersPage = () => {
  const navigate = useNavigate();
  const { } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/orders`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setOrders(data.orders);
      }
    } catch (error) {
      toast.error('Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock size={20} color="#f59e0b" />;
      case 'processing':
        return <Package size={20} color="#3b82f6" />;
      case 'completed':
        return <CheckCircle size={20} color="#10b981" />;
      case 'cancelled':
        return <XCircle size={20} color="#ef4444" />;
      default:
        return <Clock size={20} color="#64748b" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return '#f59e0b';
      case 'processing':
        return '#3b82f6';
      case 'completed':
        return '#10b981';
      case 'cancelled':
        return '#ef4444';
      default:
        return '#64748b';
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '2rem'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '1rem',
          padding: '1.5rem',
          marginBottom: '2rem',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <button
            onClick={() => navigate('/dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'none',
              border: 'none',
              color: '#667eea',
              cursor: 'pointer',
              fontSize: '1rem',
              marginBottom: '1rem'
            }}
          >
            <ArrowLeft size={20} />
            Back to Dashboard
          </button>
          <h1 style={{ margin: 0, color: '#1e293b', fontSize: '2rem' }}>
            My Orders
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#64748b' }}>
            Track and manage your medicine orders
          </p>
        </div>

        {/* Orders List */}
        {loading ? (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '1rem',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }}>
            <div className="pulse" style={{ fontSize: '2rem' }}>📦</div>
            <p style={{ marginTop: '1rem', color: '#64748b' }}>Loading orders...</p>
          </div>
        ) : orders.length === 0 ? (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '1rem',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }}>
            <Package size={64} color="#cbd5e1" />
            <h3 style={{ marginTop: '1rem', color: '#64748b' }}>No orders yet</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
              Start by placing your first order
            </p>
            <button
              onClick={() => navigate('/order')}
              style={{
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                color: 'white',
                border: 'none',
                padding: '0.75rem 2rem',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              Place Order
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {orders.map((order) => (
              <div
                key={order._id}
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '1rem',
                  padding: '1.5rem',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                  transition: 'transform 0.2s',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      {getStatusIcon(order.status)}
                      <span style={{
                        color: getStatusColor(order.status),
                        fontWeight: '600',
                        textTransform: 'capitalize'
                      }}>
                        {order.status}
                      </span>
                    </div>
                    <p style={{ margin: 0, color: '#64748b', fontSize: '0.875rem' }}>
                      Order #{order._id.slice(-8)}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1e293b' }}>
                      ₹{order.totalAmount?.toFixed(2) || '0.00'}
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.875rem' }}>
                      {new Date(order.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Items */}
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', color: '#475569', fontSize: '0.875rem', fontWeight: '600' }}>
                    Items ({order.items?.length || 0})
                  </h4>
                  {order.items?.map((item, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.5rem',
                        background: '#f8fafc',
                        borderRadius: '0.5rem',
                        marginBottom: '0.5rem'
                      }}
                    >
                      <div>
                        <p style={{ margin: 0, fontWeight: '500', color: '#1e293b' }}>
                          {item.medicineName}
                        </p>
                        <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#64748b' }}>
                          Qty: {item.quantity}
                        </p>
                      </div>
                      <p style={{ margin: 0, fontWeight: '600', color: '#1e293b' }}>
                        ₹{item.price?.toFixed(2) || '0.00'}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Delivery Address */}
                {order.deliveryAddress && (
                  <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1rem', marginTop: '1rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0', color: '#475569', fontSize: '0.875rem', fontWeight: '600' }}>
                      Delivery Address
                    </h4>
                    <p style={{ margin: 0, color: '#64748b', fontSize: '0.875rem' }}>
                      {order.deliveryAddress}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrdersPage;
