import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { TrendingUp, ArrowLeft, Calendar, Package, AlertCircle } from 'lucide-react';

const PredictionsPage = () => {
  const navigate = useNavigate();
  const { } = useAuth();
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/predictions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setPredictions(data.predictions || []);
      }
    } catch (error) {
      console.error('Failed to fetch predictions:', error);
      // Set empty array if endpoint doesn't exist yet
      setPredictions([]);
    } finally {
      setLoading(false);
    }
  };

  const getDaysUntilRefill = (date) => {
    if (!date) return null;
    const refillDate = new Date(date);
    const today = new Date();
    const diffTime = refillDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getUrgencyColor = (days) => {
    if (days <= 3) return '#ef4444';
    if (days <= 7) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)',
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
              color: '#a855f7',
              cursor: 'pointer',
              fontSize: '1rem',
              marginBottom: '1rem'
            }}
          >
            <ArrowLeft size={20} />
            Back to Dashboard
          </button>
          <h1 style={{ margin: 0, color: '#1e293b', fontSize: '2rem' }}>
            Refill Predictions
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#64748b' }}>
            AI-powered suggestions for medicine refills based on your order history
          </p>
        </div>

        {/* Predictions List */}
        {loading ? (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '1rem',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }}>
            <div className="pulse" style={{ fontSize: '2rem' }}>📊</div>
            <p style={{ marginTop: '1rem', color: '#64748b' }}>Analyzing your order history...</p>
          </div>
        ) : predictions.length === 0 ? (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '1rem',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
          }}>
            <TrendingUp size={64} color="#cbd5e1" />
            <h3 style={{ marginTop: '1rem', color: '#64748b' }}>No predictions available yet</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
              Place more orders to get AI-powered refill suggestions
            </p>
            <button
              onClick={() => navigate('/order')}
              style={{
                background: 'linear-gradient(135deg, #a855f7, #9333ea)',
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
            {predictions.map((prediction, index) => {
              const daysUntilRefill = getDaysUntilRefill(prediction.suggestedRefillDate);
              const urgencyColor = getUrgencyColor(daysUntilRefill);

              return (
                <div
                  key={index}
                  style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    borderRadius: '1rem',
                    padding: '1.5rem',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                    transition: 'transform 0.2s',
                    borderLeft: `4px solid ${urgencyColor}`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 0.5rem 0', color: '#1e293b', fontSize: '1.25rem' }}>
                        {prediction.medicineName}
                      </h3>
                      <p style={{ margin: 0, color: '#64748b', fontSize: '0.875rem' }}>
                        Based on your order pattern
                      </p>
                    </div>
                    {daysUntilRefill !== null && (
                      <div style={{
                        background: urgencyColor + '20',
                        color: urgencyColor,
                        padding: '0.5rem 1rem',
                        borderRadius: '0.5rem',
                        fontWeight: '600',
                        fontSize: '0.875rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <Calendar size={16} />
                        {daysUntilRefill > 0 ? `${daysUntilRefill} days` : 'Due now'}
                      </div>
                    )}
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1rem',
                    padding: '1rem',
                    background: '#f8fafc',
                    borderRadius: '0.5rem'
                  }}>
                    <div>
                      <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.75rem', color: '#64748b', fontWeight: '600' }}>
                        AVERAGE QUANTITY
                      </p>
                      <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1e293b' }}>
                        {prediction.averageQuantity || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.75rem', color: '#64748b', fontWeight: '600' }}>
                        LAST ORDER
                      </p>
                      <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1e293b' }}>
                        {prediction.lastOrderDate ? new Date(prediction.lastOrderDate).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.75rem', color: '#64748b', fontWeight: '600' }}>
                        CONFIDENCE
                      </p>
                      <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1e293b' }}>
                        {prediction.confidence ? `${(prediction.confidence * 100).toFixed(0)}%` : 'N/A'}
                      </p>
                    </div>
                  </div>

                  {daysUntilRefill !== null && daysUntilRefill <= 7 && (
                    <div style={{
                      marginTop: '1rem',
                      padding: '1rem',
                      background: urgencyColor + '10',
                      borderRadius: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem'
                    }}>
                      <AlertCircle size={20} color={urgencyColor} />
                      <p style={{ margin: 0, color: urgencyColor, fontSize: '0.875rem', fontWeight: '500' }}>
                        {daysUntilRefill <= 0
                          ? 'You may need to refill this medicine soon'
                          : `Consider ordering in the next ${daysUntilRefill} days`}
                      </p>
                    </div>
                  )}

                  <button
                    onClick={() => navigate('/order')}
                    style={{
                      marginTop: '1rem',
                      width: '100%',
                      background: 'linear-gradient(135deg, #a855f7, #9333ea)',
                      color: 'white',
                      border: 'none',
                      padding: '0.75rem',
                      borderRadius: '0.5rem',
                      fontSize: '1rem',
                      cursor: 'pointer',
                      fontWeight: '500',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <Package size={20} />
                    Order Now
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionsPage;
