import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Divider,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  IconButton,
  Fade,
  Slide,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  AutoAwesome,
  TrendingUp,
  Psychology,
  Launch,
  Assessment,
  Lightbulb,
  Speed,
  CheckCircle,
  Warning,
  Info,
  ShowChart,
  Settings
} from '@mui/icons-material';
import axios from 'axios';

const ConversationalTrainer = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [conversationState, setConversationState] = useState('initial');
  const [campaignId, setCampaignId] = useState(null);
  const [campaignConfig, setCampaignConfig] = useState(null);
  const [showCampaignPreview, setShowCampaignPreview] = useState(false);
  const [suggestedResponses, setSuggestedResponses] = useState([]);
  const [learningInsights, setLearningInsights] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startConversation();
  }, []);

  const startConversation = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post('/api/conversational-training/start', {
        user_id: 'user_123' // In real app, get from auth
      });
      
      setSessionId(response.data.session_id);
      setConversationState(response.data.state);
      setSuggestedResponses(response.data.suggested_responses || []);
      
      setMessages([{
        id: 1,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date().toISOString(),
        type: 'welcome'
      }]);
      
    } catch (error) {
      console.error('Error starting conversation:', error);
      setMessages([{
        id: 1,
        role: 'assistant',
        content: 'Hi! I\'m your AI campaign trainer. I\'ll help you create effective calling campaigns through simple conversation. What would you like to achieve?',
        timestamp: new Date().toISOString(),
        type: 'welcome'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message) => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post('/api/conversational-training/continue', {
        session_id: sessionId,
        message: message
      });

      const assistantMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date().toISOString(),
        type: response.data.state === 'launched' ? 'success' : 'default'
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationState(response.data.state);
      setSuggestedResponses(response.data.suggested_responses || []);
      
      if (response.data.campaign_id) {
        setCampaignId(response.data.campaign_id);
      }
      
      if (response.data.campaign_config) {
        setCampaignConfig(response.data.campaign_config);
      }

      // Load learning insights if available
      if (response.data.campaign_id && response.data.state === 'ready_to_deploy') {
        await loadLearningInsights(response.data.campaign_id);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Let me try to help you in a different way. Can you tell me what you\'re trying to achieve?',
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadLearningInsights = async (campaignId) => {
    try {
      const response = await axios.get(`/api/learning/insights/${campaignId}`);
      setLearningInsights(response.data.insights || []);
    } catch (error) {
      console.error('Error loading learning insights:', error);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage(inputValue);
    }
  };

  const handleSuggestedResponse = (suggestion) => {
    sendMessage(suggestion);
  };

  const MessageBubble = ({ message }) => {
    const isUser = message.role === 'user';
    const isSuccess = message.type === 'success';
    const isError = message.type === 'error';
    const isWelcome = message.type === 'welcome';

    return (
      <Fade in={true} timeout={500}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            mb: 2,
            px: 2
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1,
              maxWidth: '80%',
              flexDirection: isUser ? 'row-reverse' : 'row'
            }}
          >
            <Avatar
              sx={{
                bgcolor: isUser ? '#FFD700' : '#00C851',
                color: isUser ? '#000' : '#fff',
                width: 32,
                height: 32
              }}
            >
              {isUser ? <Person sx={{ fontSize: 18 }} /> : <SmartToy sx={{ fontSize: 18 }} />}
            </Avatar>
            
            <Paper
              elevation={isUser ? 2 : 1}
              sx={{
                p: 2,
                bgcolor: isUser ? '#FFD700' : isSuccess ? '#00C851' : isError ? '#ff4444' : '#1A1A1A',
                color: isUser ? '#000' : '#fff',
                borderRadius: 2,
                border: isWelcome ? '2px solid #FFD700' : 'none',
                boxShadow: isWelcome ? '0 0 20px rgba(255, 215, 0, 0.3)' : 'none'
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.5,
                  fontWeight: isWelcome ? 'bold' : 'normal'
                }}
              >
                {message.content}
              </Typography>
              
              {isWelcome && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoAwesome sx={{ color: '#FFD700', fontSize: 16 }} />
                  <Typography variant="caption" sx={{ color: '#FFD700', fontStyle: 'italic' }}>
                    AI-powered campaign creation
                  </Typography>
                </Box>
              )}
            </Paper>
          </Box>
        </Box>
      </Fade>
    );
  };

  const SuggestedResponses = () => {
    if (suggestedResponses.length === 0) return null;

    return (
      <Box sx={{ px: 2, mb: 2 }}>
        <Typography variant="caption" sx={{ color: '#999', mb: 1, display: 'block' }}>
          Suggested responses:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {suggestedResponses.map((suggestion, index) => (
            <Chip
              key={index}
              label={suggestion}
              variant="outlined"
              clickable
              onClick={() => handleSuggestedResponse(suggestion)}
              sx={{
                borderColor: '#FFD700',
                color: '#FFD700',
                '&:hover': {
                  borderColor: '#FFA000',
                  backgroundColor: 'rgba(255, 215, 0, 0.1)'
                }
              }}
            />
          ))}
        </Box>
      </Box>
    );
  };

  const ConversationProgress = () => {
    const states = ['initial', 'understanding_goal', 'gathering_context', 'clarifying_audience', 'optimizing_approach', 'generating_campaign', 'ready_to_deploy'];
    const stateLabels = {
      initial: 'Getting Started',
      understanding_goal: 'Understanding Goals',
      gathering_context: 'Gathering Context',
      clarifying_audience: 'Clarifying Audience',
      optimizing_approach: 'Optimizing Approach',
      generating_campaign: 'Generating Campaign',
      ready_to_deploy: 'Ready to Deploy'
    };

    const currentIndex = states.indexOf(conversationState);
    const progress = ((currentIndex + 1) / states.length) * 100;

    return (
      <Box sx={{ px: 2, py: 1, bgcolor: '#0A0A0A', borderBottom: '1px solid #333' }}>
        <Typography variant="caption" sx={{ color: '#FFD700', mb: 1, display: 'block' }}>
          {stateLabels[conversationState] || 'In Progress'}
        </Typography>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 4,
            borderRadius: 2,
            backgroundColor: '#333',
            '& .MuiLinearProgress-bar': {
              background: 'linear-gradient(90deg, #FFD700, #00C851)'
            }
          }}
        />
      </Box>
    );
  };

  const CampaignPreview = () => {
    if (!campaignConfig) return null;

    return (
      <Dialog
        open={showCampaignPreview}
        onClose={() => setShowCampaignPreview(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ color: '#FFD700', fontFamily: 'Playfair Display' }}>
          🎯 Campaign Preview
        </DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="h6" sx={{ color: '#00C851', mb: 2 }}>
              {campaignConfig.name}
            </Typography>
            
            <Typography variant="body1" sx={{ color: '#FFD700', mb: 3 }}>
              {campaignConfig.description}
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 3 }}>
              <Card sx={{ bgcolor: '#1A1A1A', border: '1px solid #333' }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ color: '#FFD700', mb: 1 }}>
                    📈 Expected Performance
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Answer Rate: {campaignConfig.projections?.answer_rate || 0}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Qualification Rate: {campaignConfig.projections?.qualification_rate || 0}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Transfer Rate: {campaignConfig.projections?.transfer_rate || 0}%
                  </Typography>
                </CardContent>
              </Card>
              
              <Card sx={{ bgcolor: '#1A1A1A', border: '1px solid #333' }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ color: '#FFD700', mb: 1 }}>
                    🤖 AI Configuration
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Conversation Stages: {Object.keys(campaignConfig.ai_prompts || {}).length}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Objection Handlers: {Object.keys(campaignConfig.objection_handlers || {}).length}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#fff' }}>
                    Transfer Triggers: {(campaignConfig.transfer_triggers || []).length}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            
            {learningInsights.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ color: '#00C851', mb: 2 }}>
                  🧠 Learning Insights Applied
                </Typography>
                {learningInsights.map((insight, index) => (
                  <Alert
                    key={index}
                    severity="info"
                    sx={{
                      mb: 1,
                      '& .MuiAlert-message': { color: '#FFD700' },
                      bgcolor: '#1A1A1A',
                      border: '1px solid #333'
                    }}
                  >
                    {insight.description}
                  </Alert>
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCampaignPreview(false)} sx={{ color: '#999' }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const QuickActions = () => {
    if (conversationState !== 'ready_to_deploy' && conversationState !== 'launched') return null;

    return (
      <Box sx={{ px: 2, py: 1, bgcolor: '#0A0A0A', borderTop: '1px solid #333' }}>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {campaignConfig && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<Assessment />}
              onClick={() => setShowCampaignPreview(true)}
              sx={{
                borderColor: '#FFD700',
                color: '#FFD700',
                '&:hover': { borderColor: '#FFA000', color: '#FFA000' }
              }}
            >
              View Campaign
            </Button>
          )}
          
          {campaignId && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<ShowChart />}
              onClick={() => window.open(`/analytics/${campaignId}`, '_blank')}
              sx={{
                borderColor: '#00C851',
                color: '#00C851',
                '&:hover': { borderColor: '#00A142', color: '#00A142' }
              }}
            >
              Analytics
            </Button>
          )}
          
          <Button
            size="small"
            variant="outlined"
            startIcon={<AutoAwesome />}
            onClick={startConversation}
            sx={{
              borderColor: '#999',
              color: '#999',
              '&:hover': { borderColor: '#FFD700', color: '#FFD700' }
            }}
          >
            New Campaign
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ 
        bgcolor: '#0A0A0A', 
        border: '1px solid #FFD700',
        borderRadius: '8px 8px 0 0'
      }}>
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography
            variant="h5"
            sx={{
              color: '#FFD700',
              fontFamily: 'Playfair Display',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1
            }}
          >
            <AutoAwesome sx={{ color: '#FFD700' }} />
            Conversational AI Trainer
          </Typography>
          <Typography variant="body2" sx={{ color: '#999', mt: 1 }}>
            Create powerful calling campaigns through simple conversation
          </Typography>
        </Box>
        <ConversationProgress />
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          bgcolor: '#111',
          py: 2,
          '&::-webkit-scrollbar': {
            width: '8px'
          },
          '&::-webkit-scrollbar-track': {
            background: '#1A1A1A'
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#FFD700',
            borderRadius: '4px'
          }
        }}
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress
              size={24}
              sx={{
                color: '#FFD700'
              }}
            />
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Suggested Responses */}
      <SuggestedResponses />

      {/* Input */}
      <Box sx={{ 
        bgcolor: '#0A0A0A', 
        p: 2, 
        borderTop: '1px solid #333',
        borderRadius: '0 0 8px 8px'
      }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                color: '#FFD700',
                '& fieldset': {
                  borderColor: '#FFD700'
                },
                '&:hover fieldset': {
                  borderColor: '#FFA000'
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#FFD700'
                }
              },
              '& .MuiInputBase-input': {
                color: '#FFD700'
              },
              '& .MuiInputBase-input::placeholder': {
                color: '#999'
              }
            }}
          />
          <IconButton
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            sx={{
              bgcolor: '#FFD700',
              color: '#000',
              '&:hover': {
                bgcolor: '#FFA000'
              },
              '&:disabled': {
                bgcolor: '#333',
                color: '#999'
              }
            }}
          >
            <Send />
          </IconButton>
        </Box>
      </Box>

      {/* Quick Actions */}
      <QuickActions />

      {/* Campaign Preview Dialog */}
      <CampaignPreview />
    </Box>
  );
};

export default ConversationalTrainer; 