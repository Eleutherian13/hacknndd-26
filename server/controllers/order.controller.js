const axios = require('axios');
const { asyncHandler, AppError } = require('../middleware/errorHandler');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

// Get user orders
const getUserOrders = asyncHandler(async (req, res) => {
  const { page = 1, limit = 10, status } = req.query;

  try {
    const response = await axios.get(`${FASTAPI_URL}/api/v1/orders/user/${req.userId}`, {
      params: { page, limit, status },
      headers: { 'X-Internal-API-Key': process.env.FASTAPI_API_KEY },
    });

    res.json({
      success: true,
      data: response.data,
    });
  } catch (error) {
    throw new AppError('Failed to fetch orders', 500);
  }
});

// Get order by ID
const getOrderById = asyncHandler(async (req, res) => {
  const { id } = req.params;

  try {
    const response = await axios.get(`${FASTAPI_URL}/api/v1/orders/${id}`, {
      headers: { 'X-Internal-API-Key': process.env.FASTAPI_API_KEY },
    });

    if (response.data.user_id !== req.userId && req.user?.role !== 'admin') {
      throw new AppError('Unauthorized', 403);
    }

    res.json({
      success: true,
      data: response.data,
    });
  } catch (error) {
    if (error.response?.status === 404) {
      throw new AppError('Order not found', 404);
    }
    throw new AppError('Failed to fetch order', 500);
  }
});

// Process order
const processOrder = asyncHandler(async (req, res) => {
  const { type, message, audio_base64, language } = req.body;

  if (!type || !['text', 'voice'].includes(type)) {
    throw new AppError('Invalid order type', 400);
  }

  let endpoint = '';
  let payload = {
    user_id: req.userId,
    language: language || req.user?.language || 'en',
  };

  if (type === 'text') {
    endpoint = '/api/v1/orders/text';
    payload.message = message;
  } else {
    endpoint = '/api/v1/orders/voice';
    payload.audio_base64 = audio_base64;
  }

  try {
    const response = await axios.post(`${FASTAPI_URL}${endpoint}`, payload, {
      headers: {
        'X-Internal-API-Key': process.env.FASTAPI_API_KEY,
        'Content-Type': 'application/json',
      },
    });

    res.json({
      success: true,
      data: response.data,
    });
  } catch (error) {
    throw new AppError(
      error.response?.data?.detail || 'Failed to process order',
      error.response?.status || 500
    );
  }
});

module.exports = { getUserOrders, getOrderById, processOrder };
