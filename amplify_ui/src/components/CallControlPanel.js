import React, { useState } from 'react';
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
  Alert
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Speed,
  VolumeUp,
  Security
} from '@mui/icons-material';

function CallControlPanel() {
  const [dialingActive, setDialingActive] = useState(false);
  const [concurrentCalls, setConcurrentCalls] = useState(25);
  const [aggressionLevel, setAggressionLevel] = useState(3);

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
              
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrow />}
                  onClick={() => setDialingActive(true)}
                  disabled={dialingActive}
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
                  startIcon={<Pause />}
                  onClick={() => setDialingActive(false)}
                  disabled={!dialingActive}
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