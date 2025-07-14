import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Speed,
  VolumeUp,
  Security
} from '@mui/icons-material';
import toast from 'react-hot-toast';

function CallControlPanel({ apiService }) {
  const [dialingActive, setDialingActive] = useState(false);
  const [concurrentCalls, setConcurrentCalls] = useState(25);
  const [aggressionLevel, setAggressionLevel] = useState(3);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [loading, setLoading] = useState(false);
  const [queueStatus, setQueueStatus] = useState({
    active_calls: 0,
    queued_calls: 0,
    total_agents: 0
  });

  // Load campaigns and queue status
  useEffect(() => {
    const loadData = async () => {
      try {
        const [campaignsData, queueData] = await Promise.all([
          apiService.getCampaigns(),
          apiService.getQueueStatus()
        ]);
        setCampaigns(campaignsData);
        setQueueStatus(queueData);
      } catch (error) {
        console.error('Failed to load control panel data:', error);
        toast.error('Failed to load campaigns');
      }
    };
    
    loadData();
    
    // Update queue status every 2 seconds
    const interval = setInterval(async () => {
      try {
        const queueData = await apiService.getQueueStatus();
        setQueueStatus(queueData);
      } catch (error) {
        console.error('Failed to update queue status:', error);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [apiService]);

  const handleStartCampaign = async () => {
    if (!selectedCampaign) {
      toast.error('Please select a campaign first');
      return;
    }
    
    setLoading(true);
    try {
      await apiService.startCampaign(selectedCampaign);
      setDialingActive(true);
      toast.success('Campaign started successfully!');
    } catch (error) {
      console.error('Failed to start campaign:', error);
      toast.error('Failed to start campaign');
    } finally {
      setLoading(false);
    }
  };

  const handlePauseCampaign = async () => {
    if (!selectedCampaign) {
      toast.error('Please select a campaign first');
      return;
    }
    
    setLoading(true);
    try {
      await apiService.pauseCampaign(selectedCampaign, 'Manual pause');
      setDialingActive(false);
      toast.success('Campaign paused successfully!');
    } catch (error) {
      console.error('Failed to pause campaign:', error);
      toast.error('Failed to pause campaign');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: 'primary.main', fontWeight: 700 }}>
        Elite Call Control Center
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%)',
            border: '2px solid #FFD700'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
                Dialing Controls
              </Typography>
              
              {/* Campaign Selection */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel sx={{ color: 'primary.main' }}>Select Campaign</InputLabel>
                <Select
                  value={selectedCampaign}
                  onChange={(e) => setSelectedCampaign(e.target.value)}
                  sx={{ color: 'white' }}
                >
                  {campaigns.map((campaign) => (
                    <MenuItem key={campaign.id} value={campaign.id}>
                      {campaign.name} ({campaign.status})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Queue Status */}
              <Box sx={{ mb: 3, p: 2, border: '1px solid #333', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ color: 'primary.main', mb: 1 }}>
                  Queue Status
                </Typography>
                <Box sx={{ display: 'flex', gap: 3 }}>
                  <Typography variant="body2">
                    Active: {queueStatus.active_calls}
                  </Typography>
                  <Typography variant="body2">
                    Queued: {queueStatus.queued_calls}
                  </Typography>
                  <Typography variant="body2">
                    Agents: {queueStatus.total_agents}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={handleStartCampaign}
                  disabled={dialingActive || loading}
                  sx={{ 
                    background: 'linear-gradient(45deg, #00C851 30%, #007E33 90%)',
                    minWidth: 120
                  }}
                >
                  START
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <Pause />}
                  onClick={handlePauseCampaign}
                  disabled={!dialingActive || loading}
                  sx={{ 
                    background: 'linear-gradient(45deg, #FF8F00 30%, #E65100 90%)',
                    minWidth: 120
                  }}
                >
                  PAUSE
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<Stop />}
                  color="error"
                  sx={{ minWidth: 120 }}
                  disabled={loading}
                >
                  STOP
                </Button>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Concurrent Calls: {concurrentCalls}
                </Typography>
                <Slider
                  value={concurrentCalls}
                  onChange={(e, newValue) => setConcurrentCalls(newValue)}
                  min={1}
                  max={100}
                  marks={[
                    { value: 1, label: 'Conservative' },
                    { value: 50, label: 'Aggressive' },
                    { value: 100, label: 'Maximum' }
                  ]}
                  sx={{
                    color: 'primary.main',
                    '& .MuiSlider-thumb': {
                      backgroundColor: 'primary.main'
                    },
                    '& .MuiSlider-track': {
                      background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)'
                    }
                  }}
                />
              </Box>

              <Chip 
                label={dialingActive ? 'ACTIVE' : 'INACTIVE'}
                color={dialingActive ? 'success' : 'error'}
                sx={{ fontWeight: 700, fontSize: '1rem' }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
                Current Status
              </Typography>
              
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h2" fontWeight={700} sx={{ color: 'success.main', mb: 1 }}>
                  {concurrentCalls}
                </Typography>
                <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                  Active Calls
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default CallControlPanel; 