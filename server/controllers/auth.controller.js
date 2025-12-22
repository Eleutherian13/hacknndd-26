const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { AppError, asyncHandler } = require('../middleware/errorHandler');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';
const JWT_REFRESH_EXPIRES_IN = process.env.JWT_REFRESH_EXPIRES_IN || '7d';

const generateToken = (userId, email) => {
  return jwt.sign({ userId, email }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
};

const generateRefreshToken = (userId) => {
  return jwt.sign({ userId }, JWT_SECRET, { expiresIn: JWT_REFRESH_EXPIRES_IN });
};

// Register
const register = asyncHandler(async (req, res) => {
  const { email, password, name, phone, language } = req.body;

  const existingUser = await User.findOne({ email });
  if (existingUser) {
    throw new AppError('Email already registered', 400);
  }

  const user = await User.create({
    email,
    password,
    name,
    phone,
    language: language || 'en',
  });

  const token = generateToken(user._id, user.email);
  const refreshToken = generateRefreshToken(user._id);

  res.status(201).json({
    success: true,
    message: 'User registered successfully',
    data: {
      user: {
        id: user._id,
        email: user.email,
        name: user.name,
        role: user.role,
        language: user.language,
      },
      token,
      refreshToken,
    },
  });
});

// Login
const login = asyncHandler(async (req, res) => {
  const { email, password } = req.body;

  const user = await User.findOne({ email }).select('+password');
  if (!user) {
    throw new AppError('Invalid email or password', 401);
  }

  const isPasswordValid = await user.comparePassword(password);
  if (!isPasswordValid) {
    throw new AppError('Invalid email or password', 401);
  }

  const token = generateToken(user._id, user.email);
  const refreshToken = generateRefreshToken(user._id);

  res.json({
    success: true,
    message: 'Login successful',
    data: {
      user: {
        id: user._id,
        email: user.email,
        name: user.name,
        role: user.role,
        language: user.language,
        onboardingCompleted: user.onboardingCompleted,
      },
      token,
      refreshToken,
    },
  });
});

// Logout
const logout = asyncHandler(async (req, res) => {
  res.json({
    success: true,
    message: 'Logout successful',
  });
});

// Refresh token
const refreshToken = asyncHandler(async (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    throw new AppError('Refresh token required', 400);
  }

  const decoded = jwt.verify(refreshToken, JWT_SECRET);
  const user = await User.findById(decoded.userId);
  
  if (!user) {
    throw new AppError('User not found', 404);
  }

  const newToken = generateToken(user._id, user.email);
  const newRefreshToken = generateRefreshToken(user._id);

  res.json({
    success: true,
    data: { token: newToken, refreshToken: newRefreshToken },
  });
});

// Get current user
const getCurrentUser = asyncHandler(async (req, res) => {
  const user = await User.findById(req.userId);
  
  if (!user) {
    throw new AppError('User not found', 404);
  }

  res.json({
    success: true,
    data: { user },
  });
});

// Update profile
const updateProfile = asyncHandler(async (req, res) => {
  const { name, phone, language, address, allergies, currentMedications } = req.body;

  const user = await User.findById(req.userId);
  if (!user) {
    throw new AppError('User not found', 404);
  }

  if (name) user.name = name;
  if (phone) user.phone = phone;
  if (language) user.language = language;
  if (address) user.address = address;
  if (allergies) user.allergies = allergies;
  if (currentMedications) user.currentMedications = currentMedications;

  await user.save();

  res.json({
    success: true,
    message: 'Profile updated successfully',
    data: { user },
  });
});

module.exports = {
  register,
  login,
  logout,
  refreshToken,
  getCurrentUser,
  updateProfile,
};
