import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  LinearProgress,
  Slider,
  Switch,
  FormControlLabel,
  IconButton,
  Divider,
  Paper
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Phone,
  MonetizationOn,
  Speed,
  Assessment,
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Star,
  Diamond,
  AccountBalance,
  Timeline,
  VolumeUp,
  Groups,
  SecurityUpdate
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

// Sample data for charts
const hourlyData = [
  { time: '09:00', calls: 45, transfers: 12, revenue: 1240 },
  { time: '10:00', calls: 62, transfers: 18, revenue: 1680 },
  { time: '11:00', calls: 58, transfers: 15, revenue: 1520 },
  { time: '12:00', calls: 71, transfers: 23, revenue: 2180 },
  { time: '13:00', calls: 55, transfers: 17, revenue: 1740 },
  { time: '14:00', calls: 68, transfers: 21, revenue: 2020 },
  { time: '15:00', calls: 72, transfers: 25, revenue: 2350 },
  { time: '16:00', calls: 65, transfers: 19, revenue: 1890 }
];

const performanceData = [
  { name: 'Qualified', value: 35, color: '#FFD700' },
  { name: 'Follow-up', value: 25, color: '#00C851' },
  { name: 'Not Interested', value: 30, color: '#FF8F00' },
  { name: 'No Answer', value: 10, color: '#757575' }
];

function DashboardView({ stats }) {
  const [campaignStatus, setCampaignStatus] = useState('running');
  const [concurrentCalls, setConcurrentCalls] = useState(25);
  const [aggressionLevel, setAggressionLevel] = useState(3);
  const [autoOptimization, setAutoOptimization] = useState(true);

  const handleCampaignControl = (action) => {
    setCampaignStatus(action);
    // Add toast notification here
  };

  const StatCard = ({ title, value, change, icon, color = 'primary', format = 'number' }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card sx={{ 
        height: '100%',
        background: `linear-gradient(135deg, ${color === 'primary' ? '#FFD700' : color === 'success' ? '#00C851' : color === 'warning' ? '#FF8F00' : '#1A1A1A'} 0%, rgba(255,255,255,0.1) 100%)`,
        border: `2px solid ${color === 'primary' ? '#FFD700' : color === 'success' ? '#00C851' : color === 'warning' ? '#FF8F00' : '#333'}`,
        color: color === 'primary' ? 'black' : 'white'
      }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              {title}
            </Typography>
            <Box sx={{ 
              p: 1, 
              borderRadius: '50%', 
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: color === 'primary' ? 'black' : 'white'
            }}>
              {icon}
            </Box>
          </Box>
          
          <Typography variant="h3" fontWeight={700} sx={{ mb: 1 }}>
            {format === 'currency' ? '$' : ''}
            <CountUp
              end={parseFloat(value)}
              duration={2.5}
              separator=","
              decimals={format === 'percentage' ? 1 : format === 'currency' ? 0 : 0}
            />
            {format === 'percentage' ? '%' : ''}
          </Typography>
          
          {change && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {change > 0 ? <TrendingUp color="success" /> : <TrendingDown color="error" />}
              <Typography variant="body2" sx={{ ml: 0.5, fontWeight: 600 }}>
                {change > 0 ? '+' : ''}{change}% vs yesterday
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );

  const ControlPanel = () => (
    <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%)' }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h5" fontWeight={600} sx={{ color: 'primary.main' }}>
            Elite Campaign Control
          </Typography>
          <Chip 
            label={campaignStatus.toUpperCase()}
            color={campaignStatus === 'running' ? 'success' : campaignStatus === 'paused' ? 'warning' : 'error'}
            sx={{ fontWeight: 700, fontSize: '0.9rem' }}
          />
        </Box>

        <Grid container spacing={3}>
          {/* Campaign Controls */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
              Campaign Controls
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={() => handleCampaignControl('running')}
                disabled={campaignStatus === 'running'}
                sx={{ 
                  background: 'linear-gradient(45deg, #00C851 30%, #007E33 90%)',
                  minWidth: 100
                }}
              >
                Start
              </Button>
              <Button
                variant="contained"
                startIcon={<Pause />}
                onClick={() => handleCampaignControl('paused')}
                disabled={campaignStatus === 'paused'}
                sx={{ 
                  background: 'linear-gradient(45deg, #FF8F00 30%, #E65100 90%)',
                  minWidth: 100
                }}
              >
                Pause
              </Button>
              <Button
                variant="contained"
                startIcon={<Stop />}
                onClick={() => handleCampaignControl('stopped')}
                disabled={campaignStatus === 'stopped'}
                color="error"
                sx={{ minWidth: 100 }}
              >
                Stop
              </Button>
            </Box>
          </Grid>

          {/* Dial Settings */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
              Dial Intensity
            </Typography>
            <Box sx={{ px: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Concurrent Calls: {concurrentCalls}
              </Typography>
              <Slider
                value={concurrentCalls}
                onChange={(e, newValue) => setConcurrentCalls(newValue)}
                min={5}
                max={100}
                marks={[
                  { value: 5, label: 'Conservative' },
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
          </Grid>

          {/* AI Optimization */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
              AI Optimization
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={autoOptimization}
                  onChange={(e) => setAutoOptimization(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-thumb': {
                      backgroundColor: 'primary.main'
                    }
                  }}
                />
              }
              label="Auto-Optimization"
              sx={{ mb: 1 }}
            />
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              AI learns and adjusts strategy in real-time
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Control Panel */}
      <ControlPanel />

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Active Calls"
            value={stats.activeCalls}
            change={8.2}
            icon={<Phone />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Today's Transfers"
            value={stats.todayTransfers}
            change={12.5}
            icon={<TrendingUp />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Revenue Generated"
            value={stats.todayRevenue}
            change={15.8}
            icon={<MonetizationOn />}
            color="primary"
            format="currency"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Transfer Rate"
            value={stats.transferRate}
            change={3.2}
            icon={<Assessment />}
            color="success"
            format="percentage"
          />
        </Grid>
      </Grid>

      {/* Charts and Analytics */}
      <Grid container spacing={3}>
        {/* Hourly Performance */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                Today's Performance Trajectory
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={hourlyData}>
                    <defs>
                      <linearGradient id="transferGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#FFD700" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#FFD700" stopOpacity={0.1}/>
                      </linearGradient>
                      <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00C851" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#00C851" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="time" stroke="#E0E0E0" />
                    <YAxis stroke="#E0E0E0" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1A1A1A', 
                        border: '1px solid #FFD700',
                        borderRadius: '8px'
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="transfers" 
                      stroke="#FFD700" 
                      fillOpacity={1} 
                      fill="url(#transferGradient)"
                      strokeWidth={3}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="revenue" 
                      stroke="#00C851" 
                      fillOpacity={1} 
                      fill="url(#revenueGradient)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Distribution */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                Call Outcomes
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={performanceData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {performanceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1A1A1A', 
                        border: '1px solid #FFD700',
                        borderRadius: '8px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
              <Box sx={{ mt: 2 }}>
                {performanceData.map((item, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box 
                      sx={{ 
                        width: 12, 
                        height: 12, 
                        backgroundColor: item.color, 
                        borderRadius: '50%', 
                        mr: 1 
                      }} 
                    />
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {item.name}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {item.value}%
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Real-time Status */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main', fontWeight: 600 }}>
                System Health
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  AI Performance: {stats.aiEfficiency}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={stats.aiEfficiency} 
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#333',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)',
                      borderRadius: 4
                    }
                  }}
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Network Quality: 98%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={98} 
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#333',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(45deg, #00C851 30%, #007E33 90%)',
                      borderRadius: 4
                    }
                  }}
                />
              </Box>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Cost Efficiency: 94%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={94} 
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#333',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(45deg, #00C851 30%, #007E33 90%)',
                      borderRadius: 4
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main', fontWeight: 600 }}>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Speed />}
                    sx={{ 
                      borderColor: 'primary.main',
                      color: 'primary.main',
                      '&:hover': { 
                        backgroundColor: 'rgba(255, 215, 0, 0.1)',
                        borderColor: 'primary.light'
                      }
                    }}
                  >
                    Boost Speed
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Assessment />}
                    sx={{ 
                      borderColor: 'secondary.main',
                      color: 'secondary.main',
                      '&:hover': { 
                        backgroundColor: 'rgba(0, 200, 81, 0.1)',
                        borderColor: 'secondary.light'
                      }
                    }}
                  >
                    View Report
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Settings />}
                    sx={{ 
                      borderColor: 'warning.main',
                      color: 'warning.main',
                      '&:hover': { 
                        backgroundColor: 'rgba(255, 143, 0, 0.1)',
                        borderColor: 'warning.light'
                      }
                    }}
                  >
                    Optimize
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SecurityUpdate />}
                    sx={{ 
                      borderColor: 'info.main',
                      color: 'info.main',
                      '&:hover': { 
                        backgroundColor: 'rgba(30, 136, 229, 0.1)',
                        borderColor: 'info.light'
                      }
                    }}
                  >
                    Security
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default DashboardView; 