import React from 'react';
import { Link } from 'react-router-dom';
import { Pill, Sparkles, ShieldCheck, Clock, ArrowRight, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { user } = useAuth();

  if (user) {
    window.location.href = '/dashboard';
    return null;
  }

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Header */}
      <header style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #e2e8f0'
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
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to="/login" className="btn-secondary btn">
              Login
            </Link>
            <Link to="/register" className="btn-primary btn">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section style={{ paddingTop: '8rem', paddingBottom: '5rem' }} className="container fade-in">
        <div style={{ textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: '#dbeafe',
            color: '#0369a1',
            padding: '0.5rem 1rem',
            borderRadius: '9999px',
            marginBottom: '1.5rem'
          }}>
            <Sparkles size={16} />
            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>AI-Powered Pharmacy Assistant</span>
          </div>
          
          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: 'bold',
            color: '#1e293b',
            marginBottom: '1.5rem',
            lineHeight: 1.2
          }}>
            Order Medicines with<br />
            <span style={{
              background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Your Voice or Text
            </span>
          </h1>
          
          <p style={{
            fontSize: '1.25rem',
            color: '#64748b',
            marginBottom: '2rem',
            maxWidth: '48rem',
            margin: '0 auto 2rem'
          }}>
            Experience the future of pharmacy with AI agents that understand you, predict your needs, 
            and ensure your safety. Available 24/7 in English, German, and Arabic.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/register" className="btn-primary btn">
              <span>Start Ordering Now</span>
              <ArrowRight size={20} />
            </Link>
            <Link to="/login" className="btn-secondary btn">
              Try Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '5rem 0', background: 'white' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
              Why Choose Mediloon?
            </h2>
            <p style={{ fontSize: '1.125rem', color: '#64748b' }}>
              Powered by advanced AI agents that work together for your health
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '2rem'
          }}>
            <FeatureCard
              icon={<MessageSquare size={40} color="#0ea5e9" />}
              title="Natural Ordering"
              description="Order medicines by simply speaking or typing in your own words"
            />
            <FeatureCard
              icon={<Clock size={40} color="#d946ef" />}
              title="Predictive Refills"
              description="AI predicts when you'll run out and suggests automatic refills"
            />
            <FeatureCard
              icon={<ShieldCheck size={40} color="#10b981" />}
              title="Safety First"
              description="Automatic prescription validation and drug interaction checking"
            />
            <FeatureCard
              icon={<Sparkles size={40} color="#a855f7" />}
              title="24/7 Available"
              description="Multi-agent AI system works round the clock"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        background: '#1e293b',
        color: 'white',
        padding: '3rem 0',
        textAlign: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Pill size={24} />
          <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Mediloon</span>
        </div>
        <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
          AI-Driven Agentic Ordering & Autonomous Pharmacy System
        </p>
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
          © 2025 Mediloon. All rights reserved.
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="card" style={{
      background: 'linear-gradient(135deg, #f9fafb 0%, #ffffff 100%)',
      transition: 'transform 0.2s, box-shadow 0.2s',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = '0 20px 25px rgba(0, 0, 0, 0.1)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
    }}>
      <div style={{ marginBottom: '1rem' }}>{icon}</div>
      <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>{title}</h3>
      <p style={{ color: '#64748b' }}>{description}</p>
    </div>
  );
}
