const { createClient } = require('redis');

let redisClient = null;

const connectRedis = async () => {
  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    
    redisClient = createClient({ url: redisUrl });

    redisClient.on('error', (err) => {
      console.error('❌ Redis Error:', err);
    });

    await redisClient.connect();
    
    return redisClient;
  } catch (error) {
    console.error('❌ Redis connection failed:', error);
    throw error;
  }
};

const getRedisClient = () => {
  if (!redisClient) {
    throw new Error('Redis not initialized');
  }
  return redisClient;
};

module.exports = { connectRedis, getRedisClient };
