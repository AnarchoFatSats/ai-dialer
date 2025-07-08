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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  AlertTitle,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  InputAdornment
} from '@mui/material';
import {
  AttachMoney,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Assessment,
  Warning,
  CheckCircle,
  Cancel,
  Speed,
  MonetizationOn,
  Savings,
  CurrencyExchange,
  Analytics,
  Timeline,
  ShowChart
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
  ComposedChart
} from 'recharts';

// Sample cost data
const costData = [
  { time: '09:00', cost: 125.50, revenue: 1240, profit: 1114.50, calls: 45 },
  { time: '10:00', cost: 168.20, revenue: 1680, profit: 1511.80, calls: 62 },
  { time: '11:00', cost: 152.80, revenue: 1520, profit: 1367.20, calls: 58 },
  { time: '12:00', cost: 192.30, revenue: 2180, profit: 1987.70, calls: 71 },
  { time: '13:00', cost: 145.60, revenue: 1740, profit: 1594.40, calls: 55 },
  { time: '14:00', cost: 174.40, revenue: 2020, profit: 1845.60, calls: 68 },
  { time: '15:00', cost: 195.80, revenue: 2350, profit: 2154.20, calls: 72 },
  { time: '16:00', cost: 161.50, revenue: 1890, profit: 1728.50, calls: 65 }
];

const apiCosts = [
  { name: 'Twilio Voice', cost: 845.32, percentage: 45, color: '#FFD700' },
  { name: 'Claude AI', cost: 623.18, percentage: 33, color: '#00C851' },
  { name: 'Deepgram STT', cost: 234.67, percentage: 12, color: '#FF8F00' },
  { name: 'ElevenLabs TTS', cost: 189.45, percentage: 10, color: '#1E88E5' }
];

const recentTransactions = [
  { id: 1, type: 'Transfer', amount: 125.50, campaign: 'Solar Leads Q1', time: '2 min ago', status: 'success' },
  { id: 2, type: 'Call Cost', amount: -8.25, campaign: 'Solar Leads Q1', time: '3 min ago', status: 'complete' },
  { id: 3, type: 'Transfer', amount: 89.75, campaign: 'HVAC Campaign', time: '5 min ago', status: 'success' },
  { id: 4, type: 'Call Cost', amount: -6.50, campaign: 'HVAC Campaign', time: '7 min ago', status: 'complete' },
  { id: 5, type: 'Transfer', amount: 156.00, campaign: 'Insurance Leads', time: '12 min ago', status: 'success' }
];

function CostMonitoringView() {
  const [budgetSettings, setBudgetSettings] = useState({
    dailyBudget: 2500,
    costPerTransferMax: 0.12,
    autoOptimization: true,
    budgetAlerts: true
  });
  
  const [realTimeStats, setRealTimeStats] = useState({
    todayCost: 1315.62,
    todayRevenue: 16620.00,
    todayProfit: 15304.38,
    costPerTransfer: 0.087,
    profitMargin: 92.1,
    transfersToday: 151,
    costPerCall: 0.032,
    budgetUsed: 52.6
  });

  const ProfitCard = ({ title, value, change, icon, format = 'currency', color = 'primary' }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card sx={{ 
        height: '100%',
        background: color === 'profit' 
          ? 'linear-gradient(135deg, #00C851 0%, #007E33 100%)' 
          : color === 'cost' 
            ? 'linear-gradient(135deg, #FF8F00 0%, #E65100 100%)'
            : 'linear-gradient(135deg, #FFD700 0%, #FFA000 100%)',
        border: '2px solid',
        borderColor: color === 'profit' ? '#00C851' : color === 'cost' ? '#FF8F00' : '#FFD700',
        color: 'white',
        boxShadow: `0 8px 32px ${color === 'profit' ? 'rgba(0, 200, 81, 0.3)' : color === 'cost' ? 'rgba(255, 143, 0, 0.3)' : 'rgba(255, 215, 0, 0.3)'}`
      }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              {title}
            </Typography>
            <Box sx={{ 
              p: 1, 
              borderRadius: '50%', 
              backgroundColor: 'rgba(255,255,255,0.2)'
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
              decimals={format === 'percentage' ? 1 : format === 'currency' ? 2 : 3}
            />
            {format === 'percentage' ? '%' : ''}
          </Typography>
          
          {change && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {change > 0 ? <TrendingUp sx={{ color: '#4CAF50' }} /> : <TrendingDown sx={{ color: '#F44336' }} />}
              <Typography variant="body2" sx={{ ml: 0.5, fontWeight: 600 }}>
                {change > 0 ? '+' : ''}{change}% vs yesterday
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );

  const BudgetAlert = ({ type, message, severity }) => (
    <Alert 
      severity={severity} 
      sx={{ 
        mb: 2,
        backgroundColor: severity === 'warning' ? 'rgba(255, 143, 0, 0.1)' : 'rgba(0, 200, 81, 0.1)',
        border: `1px solid ${severity === 'warning' ? '#FF8F00' : '#00C851'}`,
        color: 'white',
        '& .MuiAlert-icon': {
          color: severity === 'warning' ? '#FF8F00' : '#00C851'
        }
      }}
    >
      <AlertTitle sx={{ fontWeight: 600 }}>{type}</AlertTitle>
      {message}
    </Alert>
  );

  return (
    <Box>
      {/* Budget Alerts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <BudgetAlert 
            type="Cost Efficiency Alert"
            message="Your cost per transfer is 28% below target. Excellent performance!"
            severity="success"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <BudgetAlert 
            type="Budget Warning"
            message="Daily budget is 52% consumed. Consider optimizing call strategy."
            severity="warning"
          />
        </Grid>
      </Grid>

      {/* Key Financial Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <ProfitCard
            title="Today's Profit"
            value={realTimeStats.todayProfit}
            change={18.4}
            icon={<MonetizationOn />}
            color="profit"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <ProfitCard
            title="Total Revenue"
            value={realTimeStats.todayRevenue}
            change={15.2}
            icon={<AccountBalance />}
            color="revenue"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <ProfitCard
            title="Cost Per Transfer"
            value={realTimeStats.costPerTransfer}
            change={-12.5}
            icon={<CurrencyExchange />}
            color="cost"
            format="currency"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <ProfitCard
            title="Profit Margin"
            value={realTimeStats.profitMargin}
            change={4.8}
            icon={<ShowChart />}
            color="profit"
            format="percentage"
          />
        </Grid>
      </Grid>

      {/* Cost vs Revenue Chart */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                Real-Time Profit Analysis
              </Typography>
              <Box sx={{ height: 350 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={costData}>
                    <defs>
                      <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
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
                      formatter={(value, name) => [
                        `$${value.toFixed(2)}`,
                        name === 'cost' ? 'Cost' : name === 'revenue' ? 'Revenue' : 'Profit'
                      ]}
                    />
                    <Bar dataKey="cost" fill="#FF8F00" name="cost" />
                    <Area 
                      type="monotone" 
                      dataKey="profit" 
                      stroke="#00C851" 
                      fillOpacity={1} 
                      fill="url(#profitGradient)"
                      strokeWidth={3}
                      name="profit"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="revenue" 
                      stroke="#FFD700" 
                      strokeWidth={3}
                      dot={{ fill: '#FFD700', strokeWidth: 2, r: 4 }}
                      name="revenue"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* API Cost Breakdown */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                API Cost Breakdown
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h4" fontWeight={700} sx={{ color: 'primary.main', textAlign: 'center' }}>
                  $1,892.62
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'center' }}>
                  Total API Costs Today
                </Typography>
              </Box>
              
              {apiCosts.map((api, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" fontWeight={600}>
                      {api.name}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      ${api.cost.toFixed(2)}
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={api.percentage} 
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#333',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: api.color,
                        borderRadius: 4
                      }
                    }}
                  />
                  <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
                    {api.percentage}% of total
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Budget Controls & Recent Transactions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                Budget Controls
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Daily Budget: ${budgetSettings.dailyBudget}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={realTimeStats.budgetUsed}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: '#333',
                        '& .MuiLinearProgress-bar': {
                          background: realTimeStats.budgetUsed > 80 
                            ? 'linear-gradient(45deg, #FF1744 30%, #C62828 90%)' 
                            : realTimeStats.budgetUsed > 60 
                              ? 'linear-gradient(45deg, #FF8F00 30%, #E65100 90%)'
                              : 'linear-gradient(45deg, #00C851 30%, #007E33 90%)',
                          borderRadius: 6
                        }
                      }}
                    />
                  </Box>
                  <Typography variant="body2" sx={{ minWidth: 40 }}>
                    {realTimeStats.budgetUsed.toFixed(1)}%
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  ${(budgetSettings.dailyBudget * realTimeStats.budgetUsed / 100).toFixed(2)} used of ${budgetSettings.dailyBudget}
                </Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Max Cost Per Transfer: ${budgetSettings.costPerTransferMax.toFixed(3)}
                </Typography>
                <Slider
                  value={budgetSettings.costPerTransferMax}
                  onChange={(e, newValue) => setBudgetSettings({...budgetSettings, costPerTransferMax: newValue})}
                  min={0.05}
                  max={0.25}
                  step={0.005}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `$${value.toFixed(3)}`}
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

              <FormControlLabel
                control={
                  <Switch
                    checked={budgetSettings.autoOptimization}
                    onChange={(e) => setBudgetSettings({...budgetSettings, autoOptimization: e.target.checked})}
                    sx={{
                      '& .MuiSwitch-thumb': {
                        backgroundColor: 'primary.main'
                      }
                    }}
                  />
                }
                label="Auto Budget Optimization"
                sx={{ mb: 2 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={budgetSettings.budgetAlerts}
                    onChange={(e) => setBudgetSettings({...budgetSettings, budgetAlerts: e.target.checked})}
                    sx={{
                      '& .MuiSwitch-thumb': {
                        backgroundColor: 'primary.main'
                      }
                    }}
                  />
                }
                label="Budget Alerts"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main', fontWeight: 600 }}>
                Recent Transactions
              </Typography>
              
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Type</TableCell>
                      <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Amount</TableCell>
                      <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Campaign</TableCell>
                      <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentTransactions.map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {transaction.status === 'success' ? (
                              <CheckCircle sx={{ color: 'success.main', mr: 1, fontSize: 16 }} />
                            ) : (
                              <Cancel sx={{ color: 'warning.main', mr: 1, fontSize: 16 }} />
                            )}
                            <Typography variant="body2" fontWeight={600}>
                              {transaction.type}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            fontWeight={600}
                            sx={{ 
                              color: transaction.amount > 0 ? 'success.main' : 'warning.main' 
                            }}
                          >
                            {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                            {transaction.campaign}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                            {transaction.time}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default CostMonitoringView; 