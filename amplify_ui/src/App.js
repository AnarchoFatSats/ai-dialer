import React, { useState, useEffect } from 'react';
import {
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  IconButton,
  Badge,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
  LinearProgress,
  Button,
  Fab
} from '@mui/material';
import {
  Dashboard,
  Phone,
  Analytics,
  Settings,
  AccountBalance,
  TrendingUp,
  Notifications,
  PowerSettingsNew,
  Speed,
  AttachMoney,
  Groups,
  Assessment,
  Security,
  VolumeUp,
  Star,
  Diamond,
  MonetizationOn,
  Timeline,
  Psychology
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import DashboardView from './components/DashboardView';
import CallControlPanel from './components/CallControlPanel';
import AnalyticsView from './components/AnalyticsView';
import CostMonitoringView from './components/CostMonitoringView';
import RealTimeCallMonitor from './components/RealTimeCallMonitor';
import AITrainingView from './components/AITrainingView';
import './App.css';

// Luxury Theme - Money, Power, Opportunity
const luxuryTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#FFD700', // Rich Gold
      dark: '#B8860B', // Dark Goldenrod
      light: '#FFFF66', // Light Gold
      contrastText: '#000000'
    },
    secondary: {
      main: '#00C851', // Emerald Green
      dark: '#007E33', // Dark Emerald
      light: '#4CAF50', // Light Emerald
      contrastText: '#FFFFFF'
    },
    background: {
      default: '#0A0A0A', // Rich Black
      paper: '#1A1A1A', // Charcoal
    },
    surface: {
      main: '#2A2A2A', // Medium Gray
      dark: '#1A1A1A', // Dark Gray
      light: '#3A3A3A' // Light Gray
    },
    text: {
      primary: '#FFFFFF', // White
      secondary: '#E0E0E0', // Light Gray
      disabled: '#757575'
    },
    success: {
      main: '#00C851', // Success Green
      dark: '#007E33',
      light: '#4CAF50'
    },
    warning: {
      main: '#FF8F00', // Amber Warning
      dark: '#E65100',
      light: '#FFA726'
    },
    error: {
      main: '#FF1744', // Error Red
      dark: '#C62828',
      light: '#EF5350'
    },
    info: {
      main: '#1E88E5', // Info Blue
      dark: '#1565C0',
      light: '#42A5F5'
    }
  },
  typography: {
    fontFamily: '"Playfair Display", "Roboto", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3.5rem',
      color: '#FFD700',
      textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
    },
    h2: {
      fontWeight: 600,
      fontSize: '2.8rem',
      color: '#FFD700'
    },
    h3: {
      fontWeight: 600,
      fontSize: '2.2rem',
      color: '#FFFFFF'
    },
    h4: {
      fontWeight: 500,
      fontSize: '1.8rem',
      color: '#E0E0E0'
    },
    h5: {
      fontWeight: 500,
      fontSize: '1.4rem',
      color: '#E0E0E0'
    },
    h6: {
      fontWeight: 500,
      fontSize: '1.2rem',
      color: '#E0E0E0'
    },
    body1: {
      fontSize: '1rem',
      color: '#E0E0E0'
    },
    body2: {
      fontSize: '0.875rem',
      color: '#BDBDBD'
    }
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1A1A1A',
          border: '1px solid #333333',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(255, 215, 0, 0.1)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0 12px 48px rgba(255, 215, 0, 0.2)',
            transform: 'translateY(-2px)',
            borderColor: '#FFD700'
          }
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 600,
          boxShadow: '0 4px 16px rgba(255, 215, 0, 0.3)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0 8px 24px rgba(255, 215, 0, 0.4)',
            transform: 'translateY(-1px)'
          }
        },
        contained: {
          background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)',
          color: '#000000',
          '&:hover': {
            background: 'linear-gradient(45deg, #FFA000 30%, #FFD700 90%)'
          }
        }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(26, 26, 26, 0.95)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid #333333'
        }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          '&.success': {
            backgroundColor: '#00C851',
            color: '#FFFFFF'
          },
          '&.warning': {
            backgroundColor: '#FF8F00',
            color: '#000000'
          },
          '&.error': {
            backgroundColor: '#FF1744',
            color: '#FFFFFF'
          }
        }
      }
    }
  }
});

const sidebarItems = [
  { text: 'Dashboard', icon: <Dashboard />, view: 'dashboard' },
  { text: 'Call Control', icon: <Phone />, view: 'control' },
  { text: 'Analytics', icon: <Analytics />, view: 'analytics' },
  { text: 'AI Training', icon: <Psychology />, view: 'training' },
  { text: 'Cost Monitor', icon: <AttachMoney />, view: 'costs' },
  { text: 'Live Calls', icon: <VolumeUp />, view: 'calls' },
  { text: 'Settings', icon: <Settings />, view: 'settings' }
];

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [stats, setStats] = useState({
    activeCalls: 0,
    todayTransfers: 0,
    todayRevenue: 0,
    costPerTransfer: 0,
    transferRate: 0,
    aiEfficiency: 0
  });

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        activeCalls: Math.floor(Math.random() * 50) + 10,
        todayTransfers: Math.floor(Math.random() * 200) + 150,
        todayRevenue: Math.floor(Math.random() * 10000) + 25000,
        costPerTransfer: (Math.random() * 0.1 + 0.08).toFixed(3),
        transferRate: (Math.random() * 10 + 15).toFixed(1),
        aiEfficiency: (Math.random() * 20 + 80).toFixed(1)
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView stats={stats} />;
      case 'control':
        return <CallControlPanel />;
      case 'analytics':
        return <AnalyticsView />;
      case 'training':
        return <AITrainingView />;
      case 'costs':
        return <CostMonitoringView />;
      case 'calls':
        return <RealTimeCallMonitor />;
      default:
        return <DashboardView stats={stats} />;
    }
  };

  return (
    <ThemeProvider theme={luxuryTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        
        {/* Sidebar */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          sx={{
            width: 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
              backgroundColor: '#0A0A0A',
              borderRight: '2px solid #FFD700',
              background: 'linear-gradient(180deg, #0A0A0A 0%, #1A1A1A 100%)'
            }
          }}
        >
          <Box sx={{ p: 3, borderBottom: '1px solid #333' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar
                sx={{
                  backgroundColor: 'primary.main',
                  color: 'black',
                  mr: 2,
                  width: 48,
                  height: 48
                }}
              >
                <Diamond />
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 700 }}>
                  REACH
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  Elite Edition
                </Typography>
              </Box>
            </Box>
            
            {/* Quick Stats */}
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Card sx={{ 
                  p: 1, 
                  textAlign: 'center',
                  background: 'linear-gradient(135deg, #FFD700 0%, #FFA000 100%)',
                  color: 'black'
                }}>
                  <Typography variant="body2" fontWeight={600}>Active</Typography>
                  <Typography variant="h6" fontWeight={700}>{stats.activeCalls}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card sx={{ 
                  p: 1, 
                  textAlign: 'center',
                  background: 'linear-gradient(135deg, #00C851 0%, #007E33 100%)'
                }}>
                  <Typography variant="body2" fontWeight={600}>Rate</Typography>
                  <Typography variant="h6" fontWeight={700}>{stats.transferRate}%</Typography>
                </Card>
              </Grid>
            </Grid>
          </Box>

          <List sx={{ pt: 2 }}>
            {sidebarItems.map((item) => (
              <ListItem
                button
                key={item.text}
                onClick={() => setCurrentView(item.view)}
                sx={{
                  mx: 1,
                  mb: 0.5,
                  borderRadius: 2,
                  backgroundColor: currentView === item.view ? 'primary.main' : 'transparent',
                  color: currentView === item.view ? 'black' : 'text.primary',
                  '&:hover': {
                    backgroundColor: currentView === item.view ? 'primary.dark' : 'rgba(255, 215, 0, 0.1)',
                    transform: 'translateX(4px)'
                  },
                  transition: 'all 0.3s ease'
                }}
              >
                <ListItemIcon sx={{ 
                  color: currentView === item.view ? 'black' : 'primary.main',
                  minWidth: 40
                }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: currentView === item.view ? 700 : 500
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            backgroundColor: 'background.default',
            minHeight: '100vh'
          }}
        >
          {/* Top Bar */}
          <AppBar position="static" elevation={0}>
            <Toolbar sx={{ justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <IconButton
                  color="inherit"
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  sx={{ mr: 2 }}
                >
                  <PowerSettingsNew />
                </IconButton>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  Reach Dashboard
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {/* Revenue Display */}
                <motion.div
                  animate={{ 
                    boxShadow: [
                      '0 0 20px rgba(255, 215, 0, 0.3)',
                      '0 0 30px rgba(255, 215, 0, 0.6)',
                      '0 0 20px rgba(255, 215, 0, 0.3)'
                    ]
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Card sx={{ 
                    px: 2, 
                    py: 1,
                    background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)',
                    color: 'black'
                  }}>
                    <Typography variant="body2" fontWeight={600}>Today's Revenue</Typography>
                    <Typography variant="h6" fontWeight={700}>
                      ${stats.todayRevenue.toLocaleString()}
                    </Typography>
                  </Card>
                </motion.div>

                <IconButton color="inherit">
                  <Badge badgeContent={4} color="error">
                    <Notifications />
                  </Badge>
                </IconButton>

                <Avatar sx={{ 
                  backgroundColor: 'primary.main',
                  color: 'black',
                  fontWeight: 700
                }}>
                  AI
                </Avatar>
              </Box>
            </Toolbar>
          </AppBar>

          {/* Content Area */}
          <Container maxWidth="xl" sx={{ py: 3 }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentView}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {renderCurrentView()}
              </motion.div>
            </AnimatePresence>
          </Container>
        </Box>

        {/* Floating Action Button for Emergency Stop */}
        <Fab
          color="error"
          aria-label="emergency stop"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            background: 'linear-gradient(45deg, #FF1744 30%, #C62828 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #C62828 30%, #FF1744 90%)',
              transform: 'scale(1.1)'
            },
            transition: 'all 0.3s ease'
          }}
          onClick={() => toast.error('Emergency Stop Activated!')}
        >
          <PowerSettingsNew />
        </Fab>

        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1A1A1A',
              color: '#FFD700',
              border: '1px solid #FFD700'
            }
          }}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App; 