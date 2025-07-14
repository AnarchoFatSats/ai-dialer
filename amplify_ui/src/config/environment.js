// Environment configuration for the frontend
const config = {
  // Backend API URL - change this to your deployed backend URL
  API_BASE_URL: process.env.REACT_APP_BACKEND_API_URL || 'http://localhost:8000',
  
  // AWS Configuration
  AWS_REGION: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  
  // Feature Flags
  ENABLE_REAL_TIME_UPDATES: process.env.REACT_APP_ENABLE_REAL_TIME_UPDATES !== 'false',
  ENABLE_NOTIFICATIONS: process.env.REACT_APP_ENABLE_NOTIFICATIONS !== 'false',
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS !== 'false',
  
  // Development Settings
  DEBUG_MODE: process.env.REACT_APP_DEBUG_MODE === 'true',
  LOG_LEVEL: process.env.REACT_APP_LOG_LEVEL || 'info',
  
  // API Timeouts
  API_TIMEOUT: 30000,
  
  // Real-time update interval
  UPDATE_INTERVAL: 5000,
  
  // Development mode detection
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
};

export default config; 