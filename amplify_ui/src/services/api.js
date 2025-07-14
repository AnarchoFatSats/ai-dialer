import axios from 'axios';
import config from '../config/environment';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: config.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle common error scenarios
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.error('Unauthorized access - redirecting to login');
    } else if (error.response?.status === 500) {
      console.error('Server error - please try again later');
    }
    
    return Promise.reject(error);
  }
);

// API Service Class
class APIService {
  
  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  // Campaign Management
  async createCampaign(campaignData) {
    try {
      const response = await api.post('/campaigns', campaignData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create campaign: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getCampaigns(status = null) {
    try {
      const params = status ? { status } : {};
      const response = await api.get('/campaigns', { params });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch campaigns: ${error.response?.data?.detail || error.message}`);
    }
  }

  async startCampaign(campaignId) {
    try {
      const response = await api.post(`/campaigns/${campaignId}/start`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to start campaign: ${error.response?.data?.detail || error.message}`);
    }
  }

  async pauseCampaign(campaignId, reason = null) {
    try {
      const data = reason ? { reason } : {};
      const response = await api.post(`/campaigns/${campaignId}/pause`, data);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to pause campaign: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getCampaignPerformance(campaignId) {
    try {
      const response = await api.get(`/campaigns/${campaignId}/performance`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch campaign performance: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Analytics
  async getDashboardData() {
    try {
      const response = await api.get('/analytics/dashboard');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch dashboard data: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getCampaignAnalytics(campaignId, days = 7) {
    try {
      const response = await api.get(`/analytics/campaigns/${campaignId}`, {
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch campaign analytics: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getTransferStats() {
    try {
      const response = await api.get('/analytics/transfer-stats');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch transfer stats: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getAIPerformance() {
    try {
      const response = await api.get('/analytics/ai-performance');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch AI performance: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Call Management
  async initiateCall(callData) {
    try {
      const response = await api.post('/calls/initiate', callData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to initiate call: ${error.response?.data?.detail || error.message}`);
    }
  }

  async transferCall(callLogId, transferNumber) {
    try {
      const response = await api.post('/calls/transfer', {
        call_log_id: callLogId,
        transfer_number: transferNumber
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to transfer call: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getActiveCalls() {
    try {
      const response = await api.get('/calls/active');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch active calls: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getQueueStatus() {
    try {
      const response = await api.get('/calls/queue-status');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch queue status: ${error.response?.data?.detail || error.message}`);
    }
  }

  async cancelCall(callLogId) {
    try {
      const response = await api.post(`/calls/${callLogId}/cancel`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to cancel call: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Cost Optimization
  async trackCampaignCosts(campaignId) {
    try {
      const response = await api.post(`/cost/track/${campaignId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to track campaign costs: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getCostOptimization(campaignId, days = 7) {
    try {
      const response = await api.get(`/cost/optimization/${campaignId}`, {
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch cost optimization: ${error.response?.data?.detail || error.message}`);
    }
  }

  // DID Management
  async initializeDIDPool(didRequest) {
    try {
      const response = await api.post('/did/initialize', didRequest);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to initialize DID pool: ${error.response?.data?.detail || error.message}`);
    }
  }

  async rotateDIDs(campaignId) {
    try {
      const response = await api.post(`/did/rotate/${campaignId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to rotate DIDs: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getDIDPoolStatus(campaignId) {
    try {
      const response = await api.get(`/did/status/${campaignId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch DID pool status: ${error.response?.data?.detail || error.message}`);
    }
  }

  // AI Training
  async getTrainingCampaigns() {
    try {
      const response = await api.get('/ai-training/campaigns');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch training campaigns: ${error.response?.data?.detail || error.message}`);
    }
  }

  async updateCampaignPrompts(campaignId, promptData) {
    try {
      const response = await api.put(`/ai-training/prompts/${campaignId}`, promptData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update campaign prompts: ${error.response?.data?.detail || error.message}`);
    }
  }

  async updateVoiceSettings(campaignId, voiceData) {
    try {
      const response = await api.put(`/ai-training/voice-settings/${campaignId}`, voiceData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update voice settings: ${error.response?.data?.detail || error.message}`);
    }
  }

  async startAITraining(campaignId, trainingConfig) {
    try {
      const response = await api.post(`/ai-training/start-training/${campaignId}`, trainingConfig);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to start AI training: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Lead Management
  async uploadLeads(campaignId, leads) {
    try {
      const response = await api.post(`/campaigns/${campaignId}/leads`, leads);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to upload leads: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Multi-Agent System
  async getMultiAgentDashboard() {
    try {
      const response = await api.get('/api/multi-agent/dashboard');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch multi-agent dashboard: ${error.response?.data?.detail || error.message}`);
    }
  }

  async createAgentPool(agentData) {
    try {
      const formData = new FormData();
      Object.keys(agentData).forEach(key => {
        formData.append(key, agentData[key]);
      });
      
      const response = await api.post('/api/agents/pools', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create agent pool: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getAgentPerformance(agentId) {
    try {
      const response = await api.get(`/api/agents/pools/${agentId}/performance`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch agent performance: ${error.response?.data?.detail || error.message}`);
    }
  }

  async assignNumbers(agentId, numberCount, areaCodes) {
    try {
      const formData = new FormData();
      formData.append('number_count', numberCount);
      if (areaCodes) {
        formData.append('area_codes', areaCodes);
      }
      
      const response = await api.post(`/api/agents/pools/${agentId}/numbers/assign`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to assign numbers: ${error.response?.data?.detail || error.message}`);
    }
  }
}

// Export singleton instance
export const apiService = new APIService();
export default apiService; 