import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  LinearProgress,
  IconButton,
  Divider,
  Paper
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Phone,
  MonetizationOn,
  Assessment,
  PlayArrow,
  Pause,
  Stop,
  PanTool,
  Groups,
  Speed,
  Refresh
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';

function DashboardView({ stats, loading, backendConnected }) {
  const [campaignStatus, setCampaignStatus] = useState('running');

  const handleCampaignControl = (action) => {
    setCampaignStatus(action);
  };

  // Clean, simplified stat card
  const StatCard = ({ title, value, subtitle, icon, color = '#FFD700', trend = null }) => (
    <Card sx={{ 
      height: '100%',
      backgroundColor: '#1A1A1A',
      border: `1px solid ${color}`,
      '&:hover': { 
        boxShadow: `0 4px 20px rgba(255, 215, 0, 0.3)`,
        transform: 'translateY(-2px)'
      },
      transition: 'all 0.3s ease'
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle1" sx={{ color: '#E0E0E0', fontWeight: 500 }}>
            {title}
          </Typography>
          <Box sx={{ 
            color: color,
            display: 'flex',
            alignItems: 'center'
          }}>
            {icon}
          </Box>
        </Box>
        
        <Typography variant="h4" sx={{ 
          color: 'white', 
          fontWeight: 700, 
          mb: 1,
          fontSize: '2rem'
        }}>
          <CountUp
            end={parseFloat(value) || 0}
            duration={2}
            separator=","
            decimals={title.includes('Rate') || title.includes('%') ? 1 : 0}
          />
          {title.includes('Rate') || title.includes('%') ? '%' : ''}
          {title.includes('Revenue') ? '$' : ''}
        </Typography>
        
        {subtitle && (
          <Typography variant="body2" sx={{ color: '#B0B0B0' }}>
            {subtitle}
          </Typography>
        )}
        
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            {trend > 0 ? 
              <TrendingUp sx={{ color: '#00C851', fontSize: 16, mr: 0.5 }} /> : 
              <TrendingDown sx={{ color: '#FF3547', fontSize: 16, mr: 0.5 }} />
            }
            <Typography variant="caption" sx={{ 
              color: trend > 0 ? '#00C851' : '#FF3547',
              fontWeight: 600
            }}>
              {trend > 0 ? '+' : ''}{trend}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  // System status component
  const SystemStatus = () => (
    <Card sx={{ backgroundColor: '#1A1A1A', border: '1px solid #FFD700' }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" sx={{ color: '#FFD700', fontWeight: 600 }}>
            System Status
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip 
              label={backendConnected ? "LIVE" : "DEMO"} 
              size="small"
              sx={{ 
                backgroundColor: backendConnected ? '#00C851' : '#FF8F00',
                color: 'white',
                fontWeight: 600
              }}
            />
            <IconButton size="small" sx={{ color: '#FFD700' }}>
              <Refresh fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Typography variant="body2" sx={{ color: '#E0E0E0', mb: 1 }}>
              AI Performance
            </Typography>
            <Typography variant="h6" sx={{ color: '#00C851', fontWeight: 600 }}>
              {stats.aiEfficiency || 85}%
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" sx={{ color: '#E0E0E0', mb: 1 }}>
              Network Quality
            </Typography>
            <Typography variant="h6" sx={{ color: '#00C851', fontWeight: 600 }}>
              98%
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" sx={{ color: '#E0E0E0', mb: 1 }}>
              Cost Efficiency
            </Typography>
            <Typography variant="h6" sx={{ color: '#00C851', fontWeight: 600 }}>
              94%
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  // Campaign control panel
  const CampaignControls = () => (
    <Card sx={{ backgroundColor: '#1A1A1A', border: '1px solid #FFD700' }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" sx={{ color: '#FFD700', fontWeight: 600 }}>
            Campaign Control
          </Typography>
          <Chip 
            label={campaignStatus.toUpperCase()}
            sx={{ 
              backgroundColor: campaignStatus === 'running' ? '#00C851' : 
                            campaignStatus === 'paused' ? '#FF8F00' : '#FF3547',
              color: 'white',
              fontWeight: 600
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant={campaignStatus === 'running' ? 'contained' : 'outlined'}
            startIcon={<PlayArrow />}
            onClick={() => handleCampaignControl('running')}
            sx={{ 
              borderColor: '#00C851',
              color: campaignStatus === 'running' ? 'white' : '#00C851',
              backgroundColor: campaignStatus === 'running' ? '#00C851' : 'transparent',
              '&:hover': { 
                backgroundColor: '#00C851',
                color: 'white'
              },
              minWidth: 100
            }}
          >
            Start
          </Button>
          <Button
            variant={campaignStatus === 'paused' ? 'contained' : 'outlined'}
            startIcon={<Pause />}
            onClick={() => handleCampaignControl('paused')}
            sx={{ 
              borderColor: '#FF8F00',
              color: campaignStatus === 'paused' ? 'white' : '#FF8F00',
              backgroundColor: campaignStatus === 'paused' ? '#FF8F00' : 'transparent',
              '&:hover': { 
                backgroundColor: '#FF8F00',
                color: 'white'
              },
              minWidth: 100
            }}
          >
            Pause
          </Button>
          <Button
            variant={campaignStatus === 'stopped' ? 'contained' : 'outlined'}
            startIcon={<Stop />}
            onClick={() => handleCampaignControl('stopped')}
            sx={{ 
              borderColor: '#FF3547',
              color: campaignStatus === 'stopped' ? 'white' : '#FF3547',
              backgroundColor: campaignStatus === 'stopped' ? '#FF3547' : 'transparent',
              '&:hover': { 
                backgroundColor: '#FF3547',
                color: 'white'
              },
              minWidth: 100
            }}
          >
            Stop
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Clean Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ 
          color: '#FFD700', 
          fontWeight: 700,
          mb: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}>
          <PanTool sx={{ fontSize: 40 }} />
          Reach AI Dashboard
        </Typography>
        <Typography variant="subtitle1" sx={{ color: '#B0B0B0' }}>
          Real-time campaign performance and system monitoring
        </Typography>
      </Box>

      {/* Key Metrics - Clean Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Active Calls"
            value={stats.activeCalls || 0}
            subtitle="Currently dialing"
            icon={<Phone />}
            color="#FFD700"
            trend={8.2}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Today's Transfers"
            value={stats.todayTransfers || 0}
            subtitle="Successful conversions"
            icon={<TrendingUp />}
            color="#00C851"
            trend={12.5}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Revenue Generated"
            value={stats.todayRevenue || 0}
            subtitle="Today's earnings"
            icon={<MonetizationOn />}
            color="#FFD700"
            trend={15.8}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Transfer Rate"
            value={stats.transferRate || 0}
            subtitle="Conversion percentage"
            icon={<Assessment />}
            color="#00C851"
            trend={3.2}
          />
        </Grid>
      </Grid>

      {/* Control Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <CampaignControls />
        </Grid>
        <Grid item xs={12} md={6}>
          <SystemStatus />
        </Grid>
      </Grid>

      {/* Performance Insights */}
      <Card sx={{ backgroundColor: '#1A1A1A', border: '1px solid #FFD700' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ color: '#FFD700', fontWeight: 600, mb: 3 }}>
            Performance Insights
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" sx={{ color: '#00C851', fontWeight: 700, mb: 1 }}>
                  {((stats.todayTransfers || 0) / Math.max((stats.activeCalls || 1) * 10, 1) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body2" sx={{ color: '#E0E0E0' }}>
                  Call Success Rate
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" sx={{ color: '#FFD700', fontWeight: 700, mb: 1 }}>
                  ${(stats.todayRevenue || 0) / Math.max(stats.todayTransfers || 1, 1)}
                </Typography>
                <Typography variant="body2" sx={{ color: '#E0E0E0' }}>
                  Revenue Per Transfer
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" sx={{ color: '#FF8F00', fontWeight: 700, mb: 1 }}>
                  ${stats.costPerTransfer || 0.08}
                </Typography>
                <Typography variant="body2" sx={{ color: '#E0E0E0' }}>
                  Cost Per Transfer
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" sx={{ color: '#00C851', fontWeight: 700, mb: 1 }}>
                  {((stats.todayRevenue || 0) / Math.max((stats.costPerTransfer || 0.08) * (stats.todayTransfers || 1), 1) * 100 - 100).toFixed(0)}%
                </Typography>
                <Typography variant="body2" sx={{ color: '#E0E0E0' }}>
                  ROI
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

export default DashboardView; 