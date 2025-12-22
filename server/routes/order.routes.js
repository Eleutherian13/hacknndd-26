const express = require('express');
const { authenticate } = require('../middleware/auth');
const { getUserOrders, getOrderById, processOrder } = require('../controllers/order.controller');

const router = express.Router();

router.use(authenticate);

router.get('/', getUserOrders);
router.get('/:id', getOrderById);
router.post('/process', processOrder);

module.exports = router;
