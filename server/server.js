const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const cookieParser = require('cookie-parser');
require('dotenv').config();

// Import configurations
const { connectDatabase } = require('./config/database');
const { connectRedis } = require('./config/redis');
const { errorHandler } = require('./middleware/errorHandler');
const { rateLimiter } = require('./middleware/rateLimiter');

// Import routes
const authRoutes = require('./routes/auth.routes');
const userRoutes = require('./routes/user.routes');
const orderRoutes = require('./routes/order.routes');
const medicineRoutes = require('./routes/medicine.routes');

// Import Socket.io handlers
const { initializeSocketIO } = require('./sockets/socketManager');

// Initialize Express
const app = express();
const httpServer = createServer(app);

// Initialize Socket.io
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3001',
    credentials: true,
  },
  transports: ['websocket', 'polling'],
});

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3001',
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());
app.use(compression());
app.use(morgan(process.env.NODE_ENV === 'development' ? 'dev' : 'combined'));

// Rate limiting
app.use('/api/', rateLimiter);

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Mediloon Express Server',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/medicines', medicineRoutes);

// Root
app.get('/', (req, res) => {
  res.json({
    message: 'Mediloon AI Pharmacy - Express Server',
    version: '1.0.0',
    services: {
      express: `http://localhost:${process.env.PORT || 3000}`,
      fastapi: process.env.FASTAPI_URL || 'http://localhost:8000',
    },
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
  });
});

// Error handler
app.use(errorHandler);

// Initialize Socket.io
initializeSocketIO(io);

// Start server
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';

const startServer = async () => {
  try {
    await connectDatabase();
    console.log('✅ MongoDB connected');

    await connectRedis();
    console.log('✅ Redis connected');

    httpServer.listen(PORT, HOST, () => {
      console.log('\n' + '='.repeat(60));
      console.log('🚀 Mediloon Express Server Started');
      console.log('='.repeat(60));
      console.log(`📍 Server: http://${HOST}:${PORT}`);
      console.log(`📍 Health: http://${HOST}:${PORT}/health`);
      console.log(`🔌 Socket.io: ws://${HOST}:${PORT}`);
      console.log(`🤖 AI Backend: ${process.env.FASTAPI_URL}`);
      console.log(`🌍 Environment: ${process.env.NODE_ENV}`);
      console.log('='.repeat(60) + '\n');
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      console.log('⚠️  SIGTERM received. Shutting down gracefully...');
      httpServer.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
      });
    });

    process.on('SIGINT', () => {
      console.log('\n⚠️  SIGINT received. Shutting down gracefully...');
      httpServer.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
      });
    });

  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

module.exports = { app, io };
