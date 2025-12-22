const express = require('express');
const { authenticate } = require('../middleware/auth');

const router = express.Router();

router.use(authenticate);

router.get('/', (req, res) => {
  res.json({ message: 'Medicine routes - proxies to AI backend' });
});

module.exports = router;
