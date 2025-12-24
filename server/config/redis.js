const { createClient } = require('redis');

let redisClient = null;

const connectRedis = async () => {
  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    
    redisClient = createClient({ url: redisUrl, socket: { connectTimeout: 5000 } });

    redisClient.on('error', (err) => {
      console.error('❌ Redis Error:', err);
    });

    await redisClient.connect();
    console.log('✅ Redis connected');
    
    return redisClient;
  } catch (error) {
    console.error('❌ Redis connection failed:', error.message);
    console.log('⚠️  Continuing without Redis...');
    // Don't throw - allow server to start in limited mode
  }
};

const getRedisClient = () => {
  if (!redisClient) {
    throw new Error('Redis not initialized');
  }
  return redisClient;
};

module.exports = { connectRedis, getRedisClient };
