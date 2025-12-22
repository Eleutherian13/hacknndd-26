const jwt = require('jsonwebtoken');
const User = require('../models/User');

const connectedUsers = new Map();

const initializeSocketIO = (io) => {
  // Authentication middleware
  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth.token || 
                    socket.handshake.headers.authorization?.replace('Bearer ', '');
      
      if (!token) {
        return next(new Error('Authentication error'));
      }

      const jwtSecret = process.env.JWT_SECRET || 'your-secret-key';
      const decoded = jwt.verify(token, jwtSecret);
      
      const user = await User.findById(decoded.userId);
      if (!user) {
        return next(new Error('User not found'));
      }

      socket.userId = decoded.userId;
      socket.user = user;
      next();
    } catch (error) {
      next(new Error('Authentication error'));
    }
  });

  // Connection handler
  io.on('connection', (socket) => {
    console.log(`✅ User connected: ${socket.userId} (${socket.user?.name})`);
    
    if (socket.userId) {
      connectedUsers.set(socket.userId, socket);
      socket.join(`user:${socket.userId}`);
      
      socket.emit('connected', {
        message: 'Connected to Mediloon real-time service',
        userId: socket.userId,
        timestamp: new Date().toISOString(),
      });
    }

    // Subscribe to orders
    socket.on('subscribe:orders', () => {
      socket.join(`orders:${socket.userId}`);
      console.log(`📦 User ${socket.userId} subscribed to orders`);
    });

    // Chat message
    socket.on('chat:message', (data) => {
      console.log(`💬 Chat from ${socket.userId}:`, data);
      socket.emit('chat:message:sent', {
        messageId: data.messageId,
        status: 'processing',
        timestamp: new Date().toISOString(),
      });
    });

    // Typing indicator
    socket.on('chat:typing', (data) => {
      socket.broadcast.to(`user:${socket.userId}`).emit('chat:typing', {
        userId: socket.userId,
        isTyping: data.isTyping,
      });
    });

    // Order status
    socket.on('order:status', (orderId) => {
      socket.emit('order:status:update', {
        orderId,
        status: 'processing',
        timestamp: new Date().toISOString(),
      });
    });

    // Admin events
    if (socket.user?.role === 'admin') {
      socket.join('admin:room');
      
      socket.on('admin:broadcast', (data) => {
        io.emit('admin:announcement', {
          message: data.message,
          from: socket.user.name,
          timestamp: new Date().toISOString(),
        });
      });
    }

    // Disconnect
    socket.on('disconnect', () => {
      console.log(`❌ User disconnected: ${socket.userId}`);
      if (socket.userId) {
        connectedUsers.delete(socket.userId);
      }
    });

    socket.on('error', (error) => {
      console.error(`❌ Socket error for ${socket.userId}:`, error);
    });
  });

  console.log('✅ Socket.io initialized');
};

// Helper functions
const sendToUser = (io, userId, event, data) => {
  io.to(`user:${userId}`).emit(event, data);
};

const broadcastOrderUpdate = (io, userId, orderData) => {
  io.to(`orders:${userId}`).emit('order:update', {
    ...orderData,
    timestamp: new Date().toISOString(),
  });
};

module.exports = { initializeSocketIO, sendToUser, broadcastOrderUpdate };
