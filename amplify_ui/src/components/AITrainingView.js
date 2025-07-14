import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  AutoAwesome,
  Settings,
  ShowChart,
  TrendingUp,
  Psychology,
  Info,
  Warning
} from '@mui/icons-material';
import ConversationalTrainer from './ConversationalTrainer';

const AITrainingView = () => {
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [showLearningInsights, setShowLearningInsights] = useState(false);
  const [continuousLearning, setContinuousLearning] = useState(true);
  const [autoOptimization, setAutoOptimization] = useState(true);
  const [campaigns, setCampaigns] = useState([]);
  const [learningStats, setLearningStats] = useState({});

  useEffect(() => {
    // Load campaigns and learning stats
    loadCampaigns();
    loadLearningStats();
  }, []);

  const loadCampaigns = async () => {
    try {
      const response = await fetch('/api/campaigns');
      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Error loading campaigns:', error);
    }
  };

  const loadLearningStats = async () => {
    try {
      // Mock learning stats for now
      setLearningStats({
        totalOptimizations: 47,
        averageImprovement: 23.5,
        activeCampaigns: 12,
        learningInsights: 156
      });
    } catch (error) {
      console.error('Error loading learning stats:', error);
    }
  };

  const LearningInsightsDialog = () => (
    <Dialog
      open={showLearningInsights}
      onClose={() => setShowLearningInsights(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle sx={{ color: '#FFD700', fontFamily: 'Playfair Display' }}>
        🧠 AI Learning Insights
      </DialogTitle>
      <DialogContent>
        <Box sx={{ py: 2 }}>
          <Alert 
            severity="info" 
            sx={{ 
              mb: 2,
              '& .MuiAlert-message': { color: '#FFD700' },
              bgcolor: '#1A1A1A',
              border: '1px solid #333'
            }}
          >
            The AI continuously learns from every call to improve performance. Here's what it has learned:
          </Alert>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 3 }}>
            <Card sx={{ bgcolor: '#1A1A1A', border: '1px solid #333' }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#00C851', mb: 2 }}>
                  📈 Performance Improvements
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', mb: 1 }}>
                  Total Optimizations: {learningStats.totalOptimizations}
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', mb: 1 }}>
                  Average Improvement: {learningStats.averageImprovement}%
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff' }}>
                  Active Learning Campaigns: {learningStats.activeCampaigns}
                </Typography>
              </CardContent>
            </Card>
            
            <Card sx={{ bgcolor: '#1A1A1A', border: '1px solid #333' }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#FFD700', mb: 2 }}>
                  🎯 Key Patterns Found
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', mb: 1 }}>
                  • Calls at 2-3 PM have 34% higher success rates
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', mb: 1 }}>
                  • Conversations with 2-3 objections perform best
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff' }}>
                  • Friendly tone increases transfers by 28%
                </Typography>
              </CardContent>
            </Card>
          </Box>
          
          <Typography variant="h6" sx={{ color: '#00C851', mb: 2 }}>
            Recent Optimizations Applied
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {[
              'Optimized objection handling for solar campaigns (+15% success)',
              'Adjusted conversation timing for insurance leads (+12% transfers)',
              'Improved greeting scripts based on sentiment analysis (+8% engagement)',
              'Enhanced transfer triggers for real estate campaigns (+19% conversions)'
            ].map((optimization, index) => (
              <Alert
                key={index}
                severity="success"
                sx={{
                  '& .MuiAlert-message': { color: '#00C851' },
                  bgcolor: '#0A0A0A',
                  border: '1px solid #00C851'
                }}
              >
                {optimization}
              </Alert>
            ))}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowLearningInsights(false)} sx={{ color: '#999' }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );

  const AdvancedOptionsDialog = () => (
    <Dialog
      open={showAdvancedOptions}
      onClose={() => setShowAdvancedOptions(false)}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ color: '#FFD700', fontFamily: 'Playfair Display' }}>
        ⚙️ Advanced Settings
      </DialogTitle>
      <DialogContent>
        <Box sx={{ py: 2 }}>
          <Alert 
            severity="info" 
            sx={{ 
              mb: 3,
              '& .MuiAlert-message': { color: '#FFD700' },
              bgcolor: '#1A1A1A',
              border: '1px solid #333'
            }}
          >
            These settings control how the AI learns and optimizes your campaigns automatically.
          </Alert>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={continuousLearning}
                  onChange={(e) => setContinuousLearning(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-thumb': { backgroundColor: '#FFD700' },
                    '& .MuiSwitch-track': { backgroundColor: '#333' }
                  }}
                />
              }
              label={
                <Box>
                  <Typography variant="body1" sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                    Continuous Learning
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999' }}>
                    AI analyzes every call and continuously improves performance
                  </Typography>
                </Box>
              }
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoOptimization}
                  onChange={(e) => setAutoOptimization(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-thumb': { backgroundColor: '#00C851' },
                    '& .MuiSwitch-track': { backgroundColor: '#333' }
                  }}
                />
              }
              label={
                <Box>
                  <Typography variant="body1" sx={{ color: '#00C851', fontWeight: 'bold' }}>
                    Auto-Optimization
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#999' }}>
                    Automatically apply proven optimizations to improve results
                  </Typography>
                </Box>
              }
            />
            
            <Divider sx={{ my: 2, borderColor: '#333' }} />
            
            <Typography variant="body2" sx={{ color: '#999', fontStyle: 'italic' }}>
              Note: These features work automatically. The conversational trainer handles all the technical complexity for you.
            </Typography>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowAdvancedOptions(false)} sx={{ color: '#999' }}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header with learning status */}
      <Box sx={{ 
        bgcolor: '#0A0A0A', 
        border: '1px solid #FFD700',
        borderRadius: '8px 8px 0 0',
        p: 2
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography
            variant="h4"
            sx={{
              color: '#FFD700',
              fontFamily: 'Playfair Display',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            <AutoAwesome sx={{ color: '#FFD700' }} />
            AI Training Center
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Psychology />}
              onClick={() => setShowLearningInsights(true)}
              sx={{
                borderColor: '#00C851',
                color: '#00C851',
                '&:hover': { borderColor: '#00A142', color: '#00A142' }
              }}
            >
              Learning Insights
            </Button>
            
            <Button
              variant="outlined"
              size="small"
              startIcon={<Settings />}
              onClick={() => setShowAdvancedOptions(true)}
              sx={{
                borderColor: '#999',
                color: '#999',
                '&:hover': { borderColor: '#FFD700', color: '#FFD700' }
              }}
            >
              Settings
            </Button>
          </Box>
        </Box>
        
        <Alert 
          severity="success" 
          sx={{ 
            '& .MuiAlert-message': { color: '#00C851' },
            bgcolor: '#0A0A0A',
            border: '1px solid #00C851'
          }}
          icon={<TrendingUp />}
        >
          <Typography variant="body2">
            <strong>AI Learning Active:</strong> {learningStats.totalOptimizations} optimizations applied, 
            {learningStats.averageImprovement}% average improvement across {learningStats.activeCampaigns} campaigns
          </Typography>
        </Alert>
      </Box>

      {/* Main conversational interface */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <ConversationalTrainer />
      </Box>

      {/* Footer info */}
      <Box sx={{ 
        bgcolor: '#0A0A0A', 
        borderTop: '1px solid #333',
        p: 2,
        borderRadius: '0 0 8px 8px'
      }}>
        <Typography variant="caption" sx={{ color: '#999', textAlign: 'center', display: 'block' }}>
          💡 The AI learns from every call to improve performance automatically. 
          No technical configuration needed - just describe your goals naturally.
        </Typography>
      </Box>

      {/* Dialogs */}
      <LearningInsightsDialog />
      <AdvancedOptionsDialog />
    </Box>
  );
};

export default AITrainingView; 