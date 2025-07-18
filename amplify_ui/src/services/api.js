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
      const response = await api.post(`/campaigns/${campaignId}/leads`, { leads });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to upload leads: ${error.response?.data?.detail || error.message}`);
    }
  }

  async uploadCSVLeads(campaignId, csvFile) {
    try {
      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('campaign_id', campaignId);
      
      const response = await api.post(`/campaigns/${campaignId}/leads/csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to upload CSV leads: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getLeads(campaignId, page = 1, limit = 100) {
    try {
      const response = await api.get(`/campaigns/${campaignId}/leads`, {
        params: { page, limit }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch leads: ${error.response?.data?.detail || error.message}`);
    }
  }

  async deleteLeads(campaignId, leadIds) {
    try {
      const response = await api.delete(`/campaigns/${campaignId}/leads`, {
        data: { lead_ids: leadIds }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to delete leads: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Conversational Training
  async startConversationalTraining(userId) {
    try {
      const response = await api.post(`/conversational-training/start?user_id=${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to start conversational training: ${error.response?.data?.detail || error.message}`);
    }
  }

  async continueConversationalTraining(sessionId, message) {
    try {
      const response = await api.post('/conversational-training/continue', {
        session_id: sessionId,
        message: message
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to continue conversational training: ${error.response?.data?.detail || error.message}`);
    }
  }

  async getLearningStats() {
    try {
      const response = await api.get('/analytics/learning-stats');
      // The backend returns { success: true, data: {...} }
      return response.data?.data || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch learning stats: ${error.response?.data?.detail || error.message}`);
    }
  }

  async startTraining(trainingConfig) {
    try {
      const response = await api.post('/training/start', trainingConfig);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to start training: ${error.response?.data?.detail || error.message}`);
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

  // Smart Lead Mapping Functions
  getNextPhoneNumber(lead) {
    if (!lead.phoneNumbers || lead.phoneNumbers.length === 0) {
      return null;
    }

    // Find the current phone number
    const currentPhone = lead.phoneNumbers[lead.currentPhoneIndex];
    
    // Check if current phone should be rotated (after 3 attempts or if marked inactive)
    if (currentPhone.attempts >= 3 || !currentPhone.isActive) {
      // Find next active phone number
      const activePhones = lead.phoneNumbers.filter(phone => phone.isActive && phone.attempts < 3);
      
      if (activePhones.length === 0) {
        // All numbers exhausted
        return null;
      }

      // Rotate to next available number
      const nextPhoneIndex = lead.phoneNumbers.findIndex(phone => 
        phone.isActive && phone.attempts < 3 && phone !== currentPhone
      );

      if (nextPhoneIndex !== -1) {
        lead.currentPhoneIndex = nextPhoneIndex;
        return lead.phoneNumbers[nextPhoneIndex];
      }
    }

    return currentPhone;
  }

  recordCallAttempt(lead, phoneNumber, result) {
    // Update the specific phone number's attempt count
    const phoneIndex = lead.phoneNumbers.findIndex(p => p.number === phoneNumber.number);
    if (phoneIndex !== -1) {
      lead.phoneNumbers[phoneIndex].attempts++;
      lead.phoneNumbers[phoneIndex].lastCalled = new Date().toISOString();
      
      // Mark as inactive if no answer after multiple attempts
      if (result === 'no_answer' && lead.phoneNumbers[phoneIndex].attempts >= 3) {
        lead.phoneNumbers[phoneIndex].isActive = false;
      }

      // If answered, mark others as lower priority temporarily
      if (result === 'answered') {
        lead.phoneNumbers.forEach((p, idx) => {
          if (idx !== phoneIndex) {
            p.attempts = Math.max(p.attempts, 1); // Deprioritize other numbers
          }
        });
      }
    }

    // Update overall lead stats
    lead.totalAttempts++;
    lead.lastModified = new Date().toISOString();

    // Determine if lead should be marked as exhausted
    const activePhones = lead.phoneNumbers.filter(p => p.isActive && p.attempts < 3);
    if (activePhones.length === 0) {
      lead.status = 'exhausted';
    } else if (result === 'answered') {
      lead.status = 'contacted';
    } else {
      lead.status = 'attempted';
    }

    return lead;
  }

  getLeadCallPriority(lead) {
    // Calculate priority score based on:
    // 1. Number of available phone numbers
    // 2. Total attempts made
    // 3. Time since last attempt
    // 4. Lead priority tag

    const activePhones = lead.phoneNumbers.filter(p => p.isActive && p.attempts < 3);
    const phoneScore = activePhones.length * 10; // More numbers = higher priority

    const attemptScore = Math.max(0, 10 - lead.totalAttempts); // Fewer attempts = higher priority

    let timeScore = 0;
    if (lead.phoneNumbers.length > 0) {
      const lastCalled = lead.phoneNumbers
        .map(p => p.lastCalled)
        .filter(Boolean)
        .sort()
        .pop();
      
      if (lastCalled) {
        const hoursSinceLastCall = (Date.now() - new Date(lastCalled).getTime()) / (1000 * 60 * 60);
        timeScore = Math.min(10, Math.floor(hoursSinceLastCall / 2)); // 2+ hours = higher priority
      } else {
        timeScore = 10; // Never called = highest priority
      }
    }

    const priorityBonus = lead.priority === 'high' ? 5 : 0;

    return phoneScore + attemptScore + timeScore + priorityBonus;
  }
}

// Export singleton instance
export const apiService = new APIService();
export default apiService; 