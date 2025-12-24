import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Send, Mic, MicOff, Loader } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function OrderPage() {
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Hello! How can I help you with your medicine order today? You can type your request or use voice if your browser supports it.',
      timestamp: new Date()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [conversationId] = useState(() => `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Initialize speech recognition - with better compatibility check
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      try {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          setMessage(transcript);
          setIsListening(false);
          toast.success('Voice captured: ' + transcript);
        };

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          setIsListening(false);
          setVoiceSupported(false);
          
          // Provide more helpful error messages
          let errorMessage = 'Voice recognition failed';
          switch(event.error) {
            case 'network':
              errorMessage = 'Network error: Speech recognition service unavailable. Please use text input instead, or check your internet connection.';
              break;
            case 'not-allowed':
              errorMessage = 'Microphone access denied. Please allow microphone permissions in your browser settings.';
              break;
            case 'no-speech':
              errorMessage = 'No speech detected. Please try again and speak clearly.';
              break;
            case 'aborted':
              errorMessage = 'Speech recognition was aborted. Please try again.';
              break;
            case 'audio-capture':
              errorMessage = 'No microphone found. Please connect a microphone and try again.';
              break;
            case 'service-not-allowed':
              errorMessage = 'Speech recognition service is not available. Please use text input instead.';
              break;
            default:
              errorMessage = `Voice recognition error: ${event.error}. Please try text input instead.`;
          }
          
          toast.error(errorMessage, { duration: 5000 });
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };

        // Mark as supported
        setVoiceSupported(true);
      } catch (err) {
        console.error('Failed to initialize speech recognition:', err);
        setVoiceSupported(false);
      }
    } else {
      console.warn('Speech Recognition not supported in this browser');
      setVoiceSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (err) {
          console.error('Error stopping speech recognition:', err);
        }
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    const currentMessage = message;
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      console.log('Sending to AI backend:', process.env.REACT_APP_AI_BACKEND_URL);
      const response = await fetch(`${process.env.REACT_APP_AI_BACKEND_URL}/api/v1/orders/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: user._id,
          conversation_id: conversationId,
          message: currentMessage,
          language: 'en'
        })
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok) {
        // Add bot response
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'bot',
          content: data.message || data.response,
          timestamp: new Date(),
          parsed_medicines: data.parsed_medicines || [],
          confidence: data.confidence || 0.0
        }]);

        // Show success toast if medicines were parsed
        if (data.parsed_medicines && data.parsed_medicines.length > 0) {
          toast.success(`Added ${data.parsed_medicines.length} medicine(s) to cart`);
        }
      } else {
        throw new Error(data.detail || 'Failed to process order');
      }
    } catch (error) {
      console.error('Order error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again or contact support.',
        timestamp: new Date()
      }]);
      toast.error('Failed to process your request');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleVoiceRecognition = () => {
    if (!voiceSupported || !recognitionRef.current) {
      toast.error('Voice recognition not available. Please use text input instead.', { duration: 3000 });
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current.stop();
        setIsListening(false);
      } catch (err) {
        console.error('Error stopping voice recognition:', err);
      }
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
        toast.success('Listening... Speak now', { duration: 2000 });
      } catch (err) {
        console.error('Error starting speech recognition:', err);
        toast.error('Could not start voice recognition. Please use text input instead.');
        setVoiceSupported(false);
      }
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e2e8f0',
        padding: '1rem 0'
      }}>
        <div className="container" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <Link to="/dashboard" style={{
            padding: '0.5rem',
            borderRadius: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            textDecoration: 'none',
            color: '#64748b',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Order Medicines</h1>
            <p style={{ fontSize: '0.875rem', color: '#64748b' }}>Chat with AI to order</p>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="container" style={{ flex: 1, padding: '2rem 1rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{
          flex: 1,
          background: 'white',
          borderRadius: '1rem',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Messages */}
          <div style={{
            flex: 1,
            padding: '2rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem'
          }}>
            {messages.map((msg) => (
              <div key={msg.id} style={{
                display: 'flex',
                justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  maxWidth: '70%',
                  padding: '1rem',
                  borderRadius: '1rem',
                  background: msg.type === 'user' 
                    ? 'linear-gradient(135deg, #0ea5e9, #d946ef)'
                    : '#f1f5f9',
                  color: msg.type === 'user' ? 'white' : '#1e293b'
                }}>
                  <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {msg.suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => setMessage(suggestion)}
                          style={{
                            padding: '0.5rem 1rem',
                            background: 'white',
                            border: '1px solid #e2e8f0',
                            borderRadius: '0.5rem',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            color: '#1e293b'
                          }}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                  <p style={{
                    fontSize: '0.75rem',
                    marginTop: '0.5rem',
                    opacity: 0.7,
                    margin: '0.5rem 0 0 0'
                  }}>
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  padding: '1rem',
                  borderRadius: '1rem',
                  background: '#f1f5f9',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <Loader size={16} className="spin" />
                  <span style={{ color: '#64748b' }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: '1.5rem',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            gap: '1rem',
            alignItems: 'center'
          }}>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                border: '1px solid #e2e8f0',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                outline: 'none'
              }}
            />
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="btn-primary btn"
              style={{
                opacity: isLoading ? 0.5 : 1,
                cursor: isLoading ? 'not-allowed' : 'pointer'
              }}
            >
              <Send size={20} />
            </button>
            <button
              onClick={toggleVoiceRecognition}
              disabled={!voiceSupported}
              className="btn-secondary btn"
              style={{
                background: isListening ? '#ef4444' : voiceSupported ? undefined : '#cbd5e1',
                color: isListening ? 'white' : undefined,
                opacity: voiceSupported ? 1 : 0.5,
                cursor: voiceSupported ? (isListening ? 'pointer' : 'pointer') : 'not-allowed'
              }}
              title={voiceSupported ? 'Click to toggle voice input' : 'Voice input not available - please use text'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
