import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  Tab,
  Tabs,
  Card,
  CardContent,
  CardActions,
  Chip,
  Alert,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  AutoAwesome,
  Settings,
  TrendingUp,
  Psychology
} from '@mui/icons-material';
import ConversationalTrainer from './ConversationalTrainer';

const AITrainingView = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [isTraining, setIsTraining] = useState(false);
  const [learningStats, setLearningStats] = useState({});

  useEffect(() => {
    // Load learning stats
    loadLearningStats();
  }, []);

  const loadLearningStats = async () => {
    try {
      const response = await fetch('/api/learning-stats');
      const data = await response.json();
      setLearningStats(data);
    } catch (error) {
      console.error('Error loading learning stats:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const startTraining = async () => {
    setIsTraining(true);
    try {
      // API call to start training
      const response = await fetch('/api/start-training', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        console.log('Training started successfully');
      }
    } catch (error) {
      console.error('Error starting training:', error);
    } finally {
      setIsTraining(false);
    }
  };

  const renderOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <AutoAwesome color="primary" sx={{ mr: 1 }} />
            AI Training Progress
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={learningStats.progress || 0} 
            sx={{ mb: 2 }}
          />
          <Typography variant="body2" color="text.secondary">
            {learningStats.progress || 0}% Complete
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <TrendingUp color="success" sx={{ mr: 1 }} />
            Performance Metrics
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip 
              label={`Success Rate: ${learningStats.successRate || 0}%`} 
              color="success" 
              size="small"
            />
            <Chip 
              label={`Total Calls: ${learningStats.totalCalls || 0}`} 
              color="primary" 
              size="small"
            />
            <Chip 
              label={`Conversions: ${learningStats.conversions || 0}`} 
              color="secondary" 
              size="small"
            />
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );

  const renderTrainingInterface = () => (
    <ConversationalTrainer />
  );

  const renderAnalytics = () => (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        <Psychology color="primary" sx={{ mr: 1 }} />
        AI Learning Analytics
      </Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Detailed analytics will be available after training sessions
      </Alert>
      {/* Analytics content will be populated here */}
    </Paper>
  );

  const renderSettings = () => (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        <Settings color="primary" sx={{ mr: 1 }} />
        Training Settings
      </Typography>
      <Alert severity="info">
        Configuration options for AI training parameters
      </Alert>
      {/* Settings content will be populated here */}
    </Paper>
  );

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Training Center
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Conversational Training" />
          <Tab label="Analytics" />
          <Tab label="Settings" />
        </Tabs>
      </Box>

      {activeTab === 0 && renderOverview()}
      {activeTab === 1 && renderTrainingInterface()}
      {activeTab === 2 && renderAnalytics()}
      {activeTab === 3 && renderSettings()}
    </Box>
  );
};

export default AITrainingView; 