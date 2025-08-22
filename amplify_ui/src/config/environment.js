// Environment configuration for the frontend
const config = {
  // Backend API URL - Prioritizes environment variables for production deployment
  // Production: Uses REACT_APP_BACKEND_API_URL from build environment
  // Development: Falls back to localhost
  API_BASE_URL: process.env.REACT_APP_BACKEND_API_URL || 
    (process.env.NODE_ENV === 'production' 
      ? 'http://ai-dialer-alb-959576006.us-east-1.elb.amazonaws.com' // ALB endpoint
      : 'http://localhost:8000'),
  
  // WebSocket URL for real-time features
  WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL || 
    (process.env.NODE_ENV === 'production'
      ? 'ws://ai-dialer-alb-959576006.us-east-1.elb.amazonaws.com'
      : 'ws://localhost:8000'),
  
  // AWS Configuration
  AWS_REGION: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  
  // Feature Flags - Controlled by environment variables
  ENABLE_REAL_TIME_UPDATES: process.env.REACT_APP_ENABLE_REAL_TIME_UPDATES !== 'false',
  ENABLE_NOTIFICATIONS: process.env.REACT_APP_ENABLE_NOTIFICATIONS !== 'false',
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS !== 'false',
  
  // Development Settings
  DEBUG_MODE: process.env.REACT_APP_DEBUG_MODE === 'true',
  LOG_LEVEL: process.env.REACT_APP_LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'error' : 'info'),
  
  // API Timeouts
  API_TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000,
  
  // Real-time update interval
  UPDATE_INTERVAL: parseInt(process.env.REACT_APP_UPDATE_INTERVAL) || 5000,
  
  // Environment detection
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
  ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT || process.env.NODE_ENV || 'development',
  
  // Mock data usage (disabled in production)
  USE_MOCK_DATA: process.env.REACT_APP_USE_MOCK_DATA === 'true' && process.env.NODE_ENV !== 'production',
  
  // Build information
  BUILD_VERSION: process.env.REACT_APP_VERSION || '1.0.0',
  BUILD_TIMESTAMP: process.env.REACT_APP_BUILD_TIME || new Date().toISOString(),
};

export default config; 