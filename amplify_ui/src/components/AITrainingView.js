import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Chip,
  IconButton,
  Divider,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Psychology,
  RecordVoiceOver,
  Campaign,
  Analytics,
  Settings,
  PlayArrow,
  Stop,
  Edit,
  Add,
  Delete,
  ExpandMore,
  Science,
  VolumeUp,
  TrendingUp,
  School,
  SmartToy,
  Lightbulb,
  Speed,
  Assignment,
  CheckCircle,
  Warning,
  Info
} from '@mui/icons-material';

const AITrainingView = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [campaigns, setCampaigns] = useState([]);
  const [conversationFlows, setConversationFlows] = useState([]);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState({
    voice_id: 'rachel',
    speed: 1.0,
    pitch: 1.0,
    emphasis: 'medium'
  });

  // Mock data - replace with actual API calls
  useEffect(() => {
    setCampaigns([
      { id: 1, name: 'Solar Energy Campaign', leads: 1250, conversion_rate: 8.2 },
      { id: 2, name: 'Insurance Leads', leads: 890, conversion_rate: 12.5 },
      { id: 3, name: 'Real Estate Prospects', leads: 650, conversion_rate: 15.8 }
    ]);
    
    setConversationFlows([
      { id: 1, name: 'Aggressive Close', success_rate: 23.4, calls_made: 1250 },
      { id: 2, name: 'Consultative Approach', success_rate: 31.2, calls_made: 890 },
      { id: 3, name: 'Educational Flow', success_rate: 18.7, calls_made: 650 }
    ]);
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const renderCampaignSelection = () => (
    <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
      <CardContent>
        <Typography variant="h6" sx={{ color: '#FFD700', fontFamily: 'Playfair Display', mb: 2 }}>
          Select Campaign for AI Training
        </Typography>
        <FormControl fullWidth>
          <InputLabel sx={{ color: '#FFD700' }}>Campaign</InputLabel>
          <Select
            value={selectedCampaign}
            onChange={(e) => setSelectedCampaign(e.target.value)}
            sx={{ 
              color: '#FFD700',
              '& .MuiOutlinedInput-notchedOutline': { borderColor: '#FFD700' }
            }}
          >
            {campaigns.map((campaign) => (
              <MenuItem key={campaign.id} value={campaign.id}>
                {campaign.name} - {campaign.leads} leads ({campaign.conversion_rate}% conversion)
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </CardContent>
    </Card>
  );

  const renderConversationBuilder = () => (
    <Grid container spacing={3}>
      {/* Conversation Flow Design */}
      <Grid item xs={12} md={8}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #00C851' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ color: '#00C851', fontFamily: 'Playfair Display' }}>
                Conversation Flow Builder
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                sx={{
                  background: 'linear-gradient(45deg, #FFD700, #FFA000)',
                  color: '#000',
                  fontWeight: 'bold',
                  '&:hover': { background: 'linear-gradient(45deg, #FFA000, #FFD700)' }
                }}
              >
                Add Stage
              </Button>
            </Box>
            
            {/* Conversation Stages */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {['GREETING', 'QUALIFICATION', 'PRESENTATION', 'OBJECTION_HANDLING', 'CLOSING', 'TRANSFER'].map((stage, index) => (
                <Accordion key={stage} sx={{ background: '#1A1A1A', border: '1px solid #333' }}>
                  <AccordionSummary expandIcon={<ExpandMore sx={{ color: '#FFD700' }} />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Chip 
                        label={index + 1} 
                        sx={{ 
                          background: 'linear-gradient(45deg, #00C851, #00A142)', 
                          color: '#fff',
                          fontWeight: 'bold'
                        }} 
                      />
                      <Typography sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                        {stage.replace('_', ' ')}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="AI Prompt Template"
                          multiline
                          rows={4}
                          defaultValue={`Generate a ${stage.toLowerCase()} response that...`}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              color: '#FFD700',
                              '& fieldset': { borderColor: '#FFD700' }
                            },
                            '& .MuiInputLabel-root': { color: '#FFD700' }
                          }}
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Success Keywords"
                          placeholder="yes, interested, sounds good, tell me more"
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              color: '#00C851',
                              '& fieldset': { borderColor: '#00C851' }
                            },
                            '& .MuiInputLabel-root': { color: '#00C851' }
                          }}
                        />
                        <TextField
                          fullWidth
                          label="Objection Keywords"
                          placeholder="no, not interested, busy, remove me"
                          sx={{
                            mt: 2,
                            '& .MuiOutlinedInput-root': {
                              color: '#ff4444',
                              '& fieldset': { borderColor: '#ff4444' }
                            },
                            '& .MuiInputLabel-root': { color: '#ff4444' }
                          }}
                        />
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      {/* Training Options */}
      <Grid item xs={12} md={4}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#FFD700', fontFamily: 'Playfair Display', mb: 2 }}>
              Training Options
            </Typography>
            
            <FormControlLabel
              control={<Switch sx={{ color: '#00C851' }} />}
              label="Auto-Learning from Successful Calls"
              sx={{ color: '#FFD700', mb: 2 }}
            />
            
            <FormControlLabel
              control={<Switch sx={{ color: '#00C851' }} />}
              label="Sentiment Analysis Training"
              sx={{ color: '#FFD700', mb: 2 }}
            />
            
            <FormControlLabel
              control={<Switch sx={{ color: '#00C851' }} />}
              label="Voice Tone Optimization"
              sx={{ color: '#FFD700', mb: 2 }}
            />
            
            <Divider sx={{ my: 2, borderColor: '#333' }} />
            
            <Typography variant="subtitle1" sx={{ color: '#00C851', mb: 2 }}>
              Training Data Sources
            </Typography>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <RecordVoiceOver sx={{ color: '#FFD700' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Call Recordings" 
                  secondary="1,245 successful calls"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Assignment sx={{ color: '#00C851' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Transcripts" 
                  secondary="2,890 conversations"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingUp sx={{ color: '#FFD700' }} />
                </ListItemIcon>
                <ListItemText 
                  primary="Performance Data" 
                  secondary="Real-time metrics"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderPromptEngineering = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#FFD700', fontFamily: 'Playfair Display', mb: 2 }}>
              Advanced Prompt Engineering
            </Typography>
            
            <TextField
              fullWidth
              label="System Prompt"
              multiline
              rows={6}
              defaultValue={`You are Sarah, a professional AI sales representative making outbound calls. Your goal is to:
1. Build rapport quickly and naturally
2. Qualify leads effectively
3. Handle objections with empathy
4. Close for next steps or transfer to specialists
5. Maintain a conversational, helpful tone

Key Instructions:
- Keep responses under 30 words
- Use the lead's name naturally
- Listen for buying signals
- Ask open-ended questions
- Handle objections with "Feel, Felt, Found" technique`}
              sx={{
                mb: 3,
                '& .MuiOutlinedInput-root': {
                  color: '#FFD700',
                  '& fieldset': { borderColor: '#FFD700' }
                },
                '& .MuiInputLabel-root': { color: '#FFD700' }
              }}
            />
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" sx={{ color: '#00C851', mb: 1 }}>
                  Conversation Parameters
                </Typography>
                <TextField
                  fullWidth
                  label="Response Length (words)"
                  type="number"
                  defaultValue={30}
                  sx={{
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      color: '#FFD700',
                      '& fieldset': { borderColor: '#FFD700' }
                    },
                    '& .MuiInputLabel-root': { color: '#FFD700' }
                  }}
                />
                <TextField
                  fullWidth
                  label="Temperature (creativity)"
                  type="number"
                  inputProps={{ min: 0, max: 1, step: 0.1 }}
                  defaultValue={0.7}
                  sx={{
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      color: '#FFD700',
                      '& fieldset': { borderColor: '#FFD700' }
                    },
                    '& .MuiInputLabel-root': { color: '#FFD700' }
                  }}
                />
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel sx={{ color: '#FFD700' }}>AI Model</InputLabel>
                  <Select
                    defaultValue="claude-3-haiku"
                    sx={{
                      color: '#FFD700',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#FFD700' }
                    }}
                  >
                    <MenuItem value="claude-3-haiku">Claude 3 Haiku (Fast)</MenuItem>
                    <MenuItem value="claude-3-sonnet">Claude 3 Sonnet (Balanced)</MenuItem>
                    <MenuItem value="claude-3-opus">Claude 3 Opus (Best)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" sx={{ color: '#00C851', mb: 1 }}>
                  Conversation Style
                </Typography>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel sx={{ color: '#FFD700' }}>Tone</InputLabel>
                  <Select
                    defaultValue="professional"
                    sx={{
                      color: '#FFD700',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#FFD700' }
                    }}
                  >
                    <MenuItem value="professional">Professional</MenuItem>
                    <MenuItem value="friendly">Friendly</MenuItem>
                    <MenuItem value="consultative">Consultative</MenuItem>
                    <MenuItem value="aggressive">Aggressive</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel sx={{ color: '#FFD700' }}>Approach</InputLabel>
                  <Select
                    defaultValue="consultative"
                    sx={{
                      color: '#FFD700',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#FFD700' }
                    }}
                  >
                    <MenuItem value="consultative">Consultative</MenuItem>
                    <MenuItem value="direct">Direct</MenuItem>
                    <MenuItem value="educational">Educational</MenuItem>
                    <MenuItem value="relationship">Relationship Building</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label="Max Objections Before Transfer"
                  type="number"
                  defaultValue={3}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFD700',
                      '& fieldset': { borderColor: '#FFD700' }
                    },
                    '& .MuiInputLabel-root': { color: '#FFD700' }
                  }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #00C851' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#00C851', fontFamily: 'Playfair Display', mb: 2 }}>
              Quick Templates
            </Typography>
            
            {[
              { name: 'High-Pressure Sales', success: 28.4, color: '#ff4444' },
              { name: 'Consultative Approach', success: 34.2, color: '#00C851' },
              { name: 'Educational First', success: 22.8, color: '#FFD700' },
              { name: 'Relationship Building', success: 41.5, color: '#00C851' }
            ].map((template, index) => (
              <Card key={index} sx={{ mb: 2, background: '#1A1A1A', border: '1px solid #333' }}>
                <CardContent sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                      {template.name}
                    </Typography>
                    <Chip 
                      label={`${template.success}% success`}
                      sx={{ 
                        background: template.color, 
                        color: '#fff',
                        fontSize: '0.75rem'
                      }}
                    />
                  </Box>
                  <Button
                    size="small"
                    sx={{ mt: 1, color: '#00C851' }}
                    onClick={() => {/* Load template */}}
                  >
                    Load Template
                  </Button>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderVoiceTraining = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#FFD700', fontFamily: 'Playfair Display', mb: 2 }}>
              Voice Customization
            </Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel sx={{ color: '#FFD700' }}>Voice Model</InputLabel>
              <Select
                value={voiceSettings.voice_id}
                onChange={(e) => setVoiceSettings({...voiceSettings, voice_id: e.target.value})}
                sx={{
                  color: '#FFD700',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#FFD700' }
                }}
              >
                <MenuItem value="rachel">Rachel (Professional Female)</MenuItem>
                <MenuItem value="daniel">Daniel (Professional Male)</MenuItem>
                <MenuItem value="sarah">Sarah (Friendly Female)</MenuItem>
                <MenuItem value="michael">Michael (Authoritative Male)</MenuItem>
              </Select>
            </FormControl>
            
            <Typography sx={{ color: '#00C851', mb: 1 }}>
              Speaking Speed: {voiceSettings.speed}x
            </Typography>
            <Box sx={{ px: 2 }}>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={voiceSettings.speed}
                onChange={(e) => setVoiceSettings({...voiceSettings, speed: parseFloat(e.target.value)})}
                style={{ width: '100%', marginBottom: '16px' }}
              />
            </Box>
            
            <Typography sx={{ color: '#00C851', mb: 1 }}>
              Voice Pitch: {voiceSettings.pitch}x
            </Typography>
            <Box sx={{ px: 2 }}>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={voiceSettings.pitch}
                onChange={(e) => setVoiceSettings({...voiceSettings, pitch: parseFloat(e.target.value)})}
                style={{ width: '100%', marginBottom: '16px' }}
              />
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<VolumeUp />}
                sx={{
                  background: 'linear-gradient(45deg, #00C851, #00A142)',
                  '&:hover': { background: 'linear-gradient(45deg, #00A142, #00C851)' }
                }}
              >
                Test Voice
              </Button>
              <Button
                variant="outlined"
                startIcon={<RecordVoiceOver />}
                sx={{
                  borderColor: '#FFD700',
                  color: '#FFD700',
                  '&:hover': { borderColor: '#FFA000', color: '#FFA000' }
                }}
              >
                Record Sample
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #00C851' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#00C851', fontFamily: 'Playfair Display', mb: 2 }}>
              Training Data Management
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2, '& .MuiAlert-message': { color: '#FFD700' } }}>
              Upload successful call recordings to improve AI responses
            </Alert>
            
            <Button
              variant="contained"
              component="label"
              startIcon={<Add />}
              sx={{
                mb: 2,
                background: 'linear-gradient(45deg, #FFD700, #FFA000)',
                color: '#000',
                '&:hover': { background: 'linear-gradient(45deg, #FFA000, #FFD700)' }
              }}
            >
              Upload Training Data
              <input type="file" hidden accept=".wav,.mp3,.json" />
            </Button>
            
            <Typography variant="subtitle1" sx={{ color: '#FFD700', mb: 1 }}>
              Training Data Sources
            </Typography>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle sx={{ color: '#00C851' }} />
                </ListItemIcon>
                <ListItemText
                  primary="High-Converting Calls"
                  secondary="1,247 calls with 40%+ success rate"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Warning sx={{ color: '#FFD700' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Objection Handling"
                  secondary="892 calls with successful objection resolution"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Info sx={{ color: '#FFD700' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Transfer Patterns"
                  secondary="654 successful transfers to human agents"
                  sx={{ color: '#FFD700' }}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderABTesting = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ color: '#FFD700', fontFamily: 'Playfair Display' }}>
                A/B Testing Dashboard
              </Typography>
              <Button
                variant="contained"
                startIcon={<Science />}
                sx={{
                  background: 'linear-gradient(45deg, #00C851, #00A142)',
                  '&:hover': { background: 'linear-gradient(45deg, #00A142, #00C851)' }
                }}
                onClick={() => setOpenDialog(true)}
              >
                New A/B Test
              </Button>
            </Box>
            
            {/* Active Tests */}
            <Typography variant="subtitle1" sx={{ color: '#00C851', mb: 2 }}>
              Active Tests
            </Typography>
            
            {conversationFlows.map((flow, index) => (
              <Card key={index} sx={{ mb: 2, background: '#1A1A1A', border: '1px solid #333' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                      {flow.name}
                    </Typography>
                    <Chip 
                      label={`${flow.success_rate}% Success Rate`}
                      sx={{ 
                        background: flow.success_rate > 25 ? '#00C851' : '#ff4444',
                        color: '#fff'
                      }}
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#999' }}>
                        Calls Made
                      </Typography>
                      <Typography sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                        {flow.calls_made.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#999' }}>
                        Conversions
                      </Typography>
                      <Typography sx={{ color: '#00C851', fontWeight: 'bold' }}>
                        {Math.round(flow.calls_made * (flow.success_rate / 100))}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#999' }}>
                        Avg Call Duration
                      </Typography>
                      <Typography sx={{ color: '#FFD700', fontWeight: 'bold' }}>
                        {Math.round(Math.random() * 60 + 90)}s
                      </Typography>
                    </Box>
                  </Box>
                  
                  <LinearProgress
                    variant="determinate"
                    value={flow.success_rate * 2}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#333',
                      '& .MuiLinearProgress-bar': {
                        background: `linear-gradient(90deg, ${flow.success_rate > 25 ? '#00C851' : '#ff4444'}, ${flow.success_rate > 25 ? '#00A142' : '#cc3333'})`
                      }
                    }}
                  />
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={4}>
        <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #00C851' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#00C851', fontFamily: 'Playfair Display', mb: 2 }}>
              Test Performance
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ color: '#FFD700', mb: 1 }}>
                Statistical Significance
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircle sx={{ color: '#00C851' }} />
                <Typography sx={{ color: '#00C851' }}>
                  95% Confidence Level
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ color: '#FFD700', mb: 1 }}>
                Winning Variant
              </Typography>
              <Typography sx={{ color: '#00C851', fontWeight: 'bold' }}>
                Consultative Approach
              </Typography>
              <Typography variant="caption" sx={{ color: '#999' }}>
                +23% higher conversion rate
              </Typography>
            </Box>
            
            <Button
              fullWidth
              variant="contained"
              sx={{
                background: 'linear-gradient(45deg, #FFD700, #FFA000)',
                color: '#000',
                fontWeight: 'bold',
                '&:hover': { background: 'linear-gradient(45deg, #FFA000, #FFD700)' }
              }}
            >
              Deploy Winner
            </Button>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderTrainingActions = () => (
    <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
      <Button
        variant="contained"
        size="large"
        startIcon={isTraining ? <Stop /> : <PlayArrow />}
        onClick={() => setIsTraining(!isTraining)}
        sx={{
          background: isTraining 
            ? 'linear-gradient(45deg, #ff4444, #cc3333)'
            : 'linear-gradient(45deg, #00C851, #00A142)',
          '&:hover': {
            background: isTraining
              ? 'linear-gradient(45deg, #cc3333, #ff4444)'
              : 'linear-gradient(45deg, #00A142, #00C851)'
          }
        }}
      >
        {isTraining ? 'Stop Training' : 'Start AI Training'}
      </Button>
      
      <Button
        variant="outlined"
        size="large"
        startIcon={<Science />}
        sx={{
          borderColor: '#FFD700',
          color: '#FFD700',
          '&:hover': { borderColor: '#FFA000', color: '#FFA000' }
        }}
      >
        Run Test Campaign
      </Button>
      
      <Button
        variant="outlined"
        size="large"
        startIcon={<Analytics />}
        sx={{
          borderColor: '#00C851',
          color: '#00C851',
          '&:hover': { borderColor: '#00A142', color: '#00A142' }
        }}
      >
        View Analytics
      </Button>
    </Box>
  );

  const tabContent = [
    renderConversationBuilder(),
    renderPromptEngineering(),
    renderVoiceTraining(),
    renderABTesting()
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography
        variant="h4"
        sx={{
          color: '#FFD700',
          fontFamily: 'Playfair Display',
          textAlign: 'center',
          mb: 3,
          textShadow: '0 0 20px rgba(255, 215, 0, 0.5)'
        }}
      >
        🤖 AI Training Center
      </Typography>
      
      {renderCampaignSelection()}
      
      {isTraining && (
        <Alert severity="info" sx={{ mb: 3, '& .MuiAlert-message': { color: '#FFD700' } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography>Training in progress...</Typography>
            <LinearProgress
              variant="determinate"
              value={trainingProgress}
              sx={{
                flexGrow: 1,
                height: 8,
                borderRadius: 4,
                backgroundColor: '#333',
                '& .MuiLinearProgress-bar': {
                  background: 'linear-gradient(90deg, #00C851, #00A142)'
                }
              }}
            />
            <Typography>{trainingProgress}%</Typography>
          </Box>
        </Alert>
      )}
      
      <Card sx={{ background: 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)', border: '1px solid #FFD700' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{
            borderBottom: '1px solid #333',
            '& .MuiTab-root': {
              color: '#999',
              '&.Mui-selected': { color: '#FFD700' }
            },
            '& .MuiTabs-indicator': { backgroundColor: '#FFD700' }
          }}
        >
          <Tab icon={<SmartToy />} label="Conversation Builder" />
          <Tab icon={<Psychology />} label="Prompt Engineering" />
          <Tab icon={<RecordVoiceOver />} label="Voice Training" />
          <Tab icon={<Science />} label="A/B Testing" />
        </Tabs>
        
        <CardContent>
          {tabContent[activeTab]}
          {renderTrainingActions()}
        </CardContent>
      </Card>

      {/* New A/B Test Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ color: '#FFD700', fontFamily: 'Playfair Display' }}>
          Create New A/B Test
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Test Name"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Variant A Description"
                multiline
                rows={3}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Success Metric"
                select
                sx={{ mb: 2 }}
              >
                <MenuItem value="conversion">Conversion Rate</MenuItem>
                <MenuItem value="transfer">Transfer Rate</MenuItem>
                <MenuItem value="duration">Call Duration</MenuItem>
              </TextField>
              <TextField
                fullWidth
                label="Variant B Description"
                multiline
                rows={3}
                sx={{ mb: 2 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} sx={{ color: '#999' }}>
            Cancel
          </Button>
          <Button 
            onClick={() => setOpenDialog(false)}
            variant="contained"
            sx={{
              background: 'linear-gradient(45deg, #FFD700, #FFA000)',
              color: '#000'
            }}
          >
            Start Test
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AITrainingView; 