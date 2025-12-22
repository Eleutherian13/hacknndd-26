import React, { createContext, useContext, useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const SocketContext = createContext();

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider');
  }
  return context;
};

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:3000';

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [orderUpdates, setOrderUpdates] = useState([]);
  const { token, user } = useAuth();

  useEffect(() => {
    if (!token) {
      if (socket) {
        socket.disconnect();
        setSocket(null);
        setConnected(false);
      }
      return;
    }

    const newSocket = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
    });

    newSocket.on('connect', () => {
      console.log('✅ Socket connected');
      setConnected(true);
    });

    newSocket.on('connected', (data) => {
      console.log('✅ Server confirmed:', data);
    });

    newSocket.on('disconnect', () => {
      console.log('❌ Socket disconnected');
      setConnected(false);
    });

    newSocket.on('error', (error) => {
      console.error('❌ Socket error:', error);
    });

    newSocket.on('order:update', (data) => {
      console.log('📦 Order update:', data);
      setOrderUpdates(prev => [data, ...prev]);
      toast.success(`Order ${data.status}`);
    });

    newSocket.on('prediction:alert', (data) => {
      console.log('🔮 Prediction:', data);
      toast.success('New prediction available');
    });

    newSocket.on('admin:announcement', (data) => {
      toast.success(data.message, { icon: '📢' });
    });

    setSocket(newSocket);

    if (user) {
      newSocket.emit('subscribe:orders');
    }

    return () => {
      newSocket.disconnect();
    };
  }, [token, user]);

  const sendChatMessage = (message) => {
    if (!socket || !connected) {
      toast.error('Not connected to server');
      return;
    }

    socket.emit('chat:message', {
      messageId: Date.now().toString(),
      message,
      timestamp: new Date().toISOString(),
    });
  };

  const value = {
    socket,
    connected,
    orderUpdates,
    sendChatMessage,
  };

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
};
