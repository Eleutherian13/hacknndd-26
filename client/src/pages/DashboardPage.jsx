import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSocket } from '../context/SocketContext';
import {
  Pill,
  MessageSquare,
  Package,
  TrendingUp,
  User,
  LogOut,
  Bell,
  Sparkles
} from 'lucide-react';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const { connected } = useSocket();

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb' }}>
      {/* Header */}
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e2e8f0',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div className="container" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '4rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Pill size={32} color="#0ea5e9" />
            <span style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Mediloon
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Connection Status */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.375rem 0.75rem',
              borderRadius: '9999px',
              background: '#f1f5f9'
            }}>
              <div style={{
                width: '0.5rem',
                height: '0.5rem',
                borderRadius: '50%',
                background: connected ? '#10b981' : '#9ca3af'
              }} className={connected ? 'pulse' : ''} />
              <span style={{ fontSize: '0.75rem', fontWeight: 500, color: '#374151' }}>
                {connected ? 'Connected' : 'Offline'}
              </span>
            </div>

            {/* Notifications */}
            <button style={{
              padding: '0.5rem',
              color: '#64748b',
              background: 'transparent',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              position: 'relative'
            }}>
              <Bell size={20} />
              <span style={{
                position: 'absolute',
                top: '0.25rem',
                right: '0.25rem',
                width: '0.5rem',
                height: '0.5rem',
                background: '#ef4444',
                borderRadius: '50%'
              }} />
            </button>

            {/* Profile */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
              <div style={{
                width: '2rem',
                height: '2rem',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 500
              }}>
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{user?.name}</span>
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              style={{
                padding: '0.5rem',
                color: '#64748b',
                background: 'transparent',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#fef2f2';
                e.currentTarget.style.color = '#ef4444';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = '#64748b';
              }}
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container" style={{ padding: '2rem 1rem' }}>
        {/* Welcome */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            Welcome back, {user?.name}! 👋
          </h1>
          <p style={{ color: '#64748b' }}>
            How can I help you with your medicines today?
          </p>
        </div>

        {/* Quick Actions */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          <QuickActionCard
            icon={<MessageSquare size={32} color="#0ea5e9" />}
            title="Order Medicines"
            description="Use voice or text"
            href="/order"
            gradient="linear-gradient(135deg, #0ea5e9, #0284c7)"
          />
          <QuickActionCard
            icon={<Package size={32} color="#10b981" />}
            title="My Orders"
            description="Track your orders"
            href="/orders"
            gradient="linear-gradient(135deg, #10b981, #059669)"
          />
          <QuickActionCard
            icon={<TrendingUp size={32} color="#a855f7" />}
            title="Predictions"
            description="Refill suggestions"
            href="/predictions"
            gradient="linear-gradient(135deg, #a855f7, #9333ea)"
          />
          <QuickActionCard
            icon={<User size={32} color="#f59e0b" />}
            title="Profile"
            description="Manage your profile"
            href="/profile"
            gradient="linear-gradient(135deg, #f59e0b, #d97706)"
          />
        </div>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem'
        }}>
          <StatsCard title="Active Orders" value="2" change="+1 this week" positive />
          <StatsCard title="Medicines Ordered" value="12" change="+3 this month" positive />
          <StatsCard title="Next Refill" value="5 days" change="Aspirin 100mg" />
        </div>

        {/* AI Status */}
        <div style={{
          background: 'linear-gradient(135deg, #dbeafe 0%, #fae8ff 100%)',
          borderRadius: '1rem',
          padding: '2rem',
          border: '1px solid #bfdbfe'
        }}>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{
              width: '3rem',
              height: '3rem',
              borderRadius: '0.75rem',
              background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Sparkles size={24} color="white" />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                AI Agents Ready to Assist
              </h3>
              <p style={{ color: '#374151', marginBottom: '1rem' }}>
                Our multi-agent system is monitoring your medicine needs and ensuring your safety 24/7.
              </p>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '1rem'
              }}>
                <AgentStatus name="Ordering" status="active" />
                <AgentStatus name="Forecast" status="active" />
                <AgentStatus name="Safety" status="active" />
                <AgentStatus name="Procurement" status="active" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickActionCard({ icon, title, description, href, gradient }) {
  return (
    <Link to={href} style={{ textDecoration: 'none' }}>
      <div className="card" style={{
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '0 20px 25px rgba(0, 0, 0, 0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
      }}>
        <div style={{
          width: '3.5rem',
          height: '3.5rem',
          borderRadius: '0.75rem',
          background: gradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1rem',
          transition: 'transform 0.2s'
        }}>
          {icon}
        </div>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.25rem', color: '#1e293b' }}>
          {title}
        </h3>
        <p style={{ fontSize: '0.875rem', color: '#64748b' }}>{description}</p>
      </div>
    </Link>
  );
}

function StatsCard({ title, value, change, positive }) {
  return (
    <div className="card">
      <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.25rem' }}>{title}</p>
      <p style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>{value}</p>
      <p style={{
        fontSize: '0.875rem',
        color: positive ? '#10b981' : '#64748b',
        background: positive ? '#d1fae5' : '#f1f5f9',
        padding: '0.25rem 0.5rem',
        borderRadius: '9999px',
        display: 'inline-block'
      }}>
        {change}
      </p>
    </div>
  );
}

function AgentStatus({ name, status }) {
  return (
    <div className="card" style={{ padding: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
        <div style={{
          width: '0.5rem',
          height: '0.5rem',
          borderRadius: '50%',
          background: status === 'active' ? '#10b981' : '#9ca3af'
        }} className={status === 'active' ? 'pulse' : ''} />
        <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>{name}</span>
      </div>
      <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
        {status === 'active' ? 'Online' : 'Offline'}
      </p>
    </div>
  );
}
