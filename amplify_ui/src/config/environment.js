// Environment configuration for AI Dialer
const environment = {
  // Production API endpoint - HTTPS secured
  API_BASE_URL: process.env.REACT_APP_BACKEND_API_URL || 'https://intelareach.com',
  
  // WebSocket endpoint for real-time updates  
  WS_BASE_URL: process.env.REACT_APP_WS_URL || 'wss://intelareach.com/ws/dashboard',
  
  // Environment settings
  LOG_LEVEL: process.env.REACT_APP_LOG_LEVEL || 'production',
  API_TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000,
  UPDATE_INTERVAL: parseInt(process.env.REACT_APP_UPDATE_INTERVAL) || 5000,
  
  // Build information
  ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT || 'production',
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
  USE_MOCK_DATA: process.env.REACT_APP_USE_MOCK_DATA === 'true' ? false : false, // Always use real data in production
  
  BUILD_VERSION: process.env.REACT_APP_VERSION || '1.0.0',
  BUILD_TIMESTAMP: process.env.REACT_APP_BUILD_TIMESTAMP || new Date().toISOString()
};

export default environment; 