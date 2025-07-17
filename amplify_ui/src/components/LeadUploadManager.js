import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Paper,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  IconButton,
  Divider
} from '@mui/material';
import {
  CloudUpload,
  Download,
  DeleteForever,
  Visibility,
  PlayArrow,
  CheckCircle,
  Warning,
  Error,
  Info,
  PanTool
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const LeadUploadManager = ({ apiService, campaigns }) => {
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [parsedLeads, setParsedLeads] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  const [uploadStats, setUploadStats] = useState({
    total: 0,
    valid: 0,
    invalid: 0,
    duplicates: 0
  });
  const fileInputRef = useRef(null);

  // Helper to find column index by header name
  const findColumn = (headers, searchTerms) => {
    for (let i = 0; i < headers.length; i++) {
      if (searchTerms.some(term => headers[i].toLowerCase().includes(term))) {
        return i;
      }
    }
    return undefined;
  };

  // Enhanced CSV parsing with smart lead mapping
  const parseCSV = (csvText) => {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      return { leads: [], errors: ['CSV file is empty or has no data rows'] };
    }

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, '').toLowerCase());
    
    // Enhanced column mapping for multiple phone numbers
    const columnMap = {
      phone: findColumn(headers, ['phone', 'phone1', 'phone_number', 'primary_phone', 'mobile', 'cell']),
      phone2: findColumn(headers, ['phone2', 'phone_2', 'secondary_phone', 'alternate_phone', 'home_phone']),
      phone3: findColumn(headers, ['phone3', 'phone_3', 'work_phone', 'office_phone', 'business_phone']),
      first_name: findColumn(headers, ['first_name', 'fname', 'first', 'firstname']),
      last_name: findColumn(headers, ['last_name', 'lname', 'last', 'lastname', 'surname']),
      email: findColumn(headers, ['email', 'email_address', 'e_mail']),
      company: findColumn(headers, ['company', 'business', 'organization', 'employer']),
      address: findColumn(headers, ['address', 'street', 'address1']),
      city: findColumn(headers, ['city', 'town']),
      state: findColumn(headers, ['state', 'province', 'region']),
      zip: findColumn(headers, ['zip', 'postal_code', 'zipcode', 'postcode'])
    };

    const leads = [];
    const errors = [];

    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(',').map(cell => cell.trim());
      const lead = {};

      // Basic info mapping
      Object.keys(columnMap).forEach(key => {
        if (columnMap[key] !== undefined && cells[columnMap[key]]) {
          lead[key] = cells[columnMap[key]].replace(/"/g, '');
        }
      });

      // Smart phone number handling
      const phoneNumbers = [];
      ['phone', 'phone2', 'phone3'].forEach(phoneField => {
        if (lead[phoneField] && /^\+?[\d\s\-\(\)]{10,}$/.test(lead[phoneField])) {
          phoneNumbers.push({
            number: lead[phoneField],
            type: phoneField === 'phone' ? 'primary' : phoneField === 'phone2' ? 'secondary' : 'tertiary',
            attempts: 0,
            lastCalled: null,
            isActive: true
          });
        }
      });

      // Validation
      if (phoneNumbers.length === 0) {
        errors.push(`Row ${i + 1}: No valid phone numbers found`);
        continue;
      }

      if (lead.email && !/\S+@\S+\.\S+/.test(lead.email)) {
        errors.push(`Row ${i + 1}: Invalid email format`);
      }

      // Enhanced lead object with smart mapping
      const enhancedLead = {
        id: `lead_${Date.now()}_${i}`,
        first_name: lead.first_name || '',
        last_name: lead.last_name || '',
        email: lead.email || '',
        company: lead.company || '',
        address: lead.address || '',
        city: lead.city || '',
        state: lead.state || '',
        zip: lead.zip || '',
        phone: phoneNumbers[0].number, // Primary phone for display
        phoneNumbers: phoneNumbers, // All phone numbers with metadata
        currentPhoneIndex: 0, // Track which phone number to use next
        totalAttempts: 0,
        status: 'new',
        priority: phoneNumbers.length > 1 ? 'high' : 'normal', // Higher priority for multiple numbers
        created_at: new Date().toISOString(),
        lastModified: new Date().toISOString(),
        tags: phoneNumbers.length > 1 ? ['multiple_numbers'] : []
      };

      leads.push(enhancedLead);
    }

    return { leads, errors };
  };

  // Smart Lead Mapping Functions
  const getNextPhoneNumber = (lead) => {
    if (!lead.phoneNumbers || lead.phoneNumbers.length === 0) {
      return null;
    }

    // Find the current phone number
    const currentPhone = lead.phoneNumbers[lead.currentPhoneIndex];
    
    // Check if current phone should be rotated (after 3 attempts or if marked inactive)
    if (currentPhone.attempts >= 3 || !currentPhone.isActive) {
      // Find next active phone number
      const activePhones = lead.phoneNumbers.filter(phone => phone.isActive && phone.attempts < 3);
      
      if (activePhones.length === 0) {
        // All numbers exhausted
        return null;
      }

      // Rotate to next available number
      const nextPhoneIndex = lead.phoneNumbers.findIndex(phone => 
        phone.isActive && phone.attempts < 3 && phone !== currentPhone
      );

      if (nextPhoneIndex !== -1) {
        lead.currentPhoneIndex = nextPhoneIndex;
        return lead.phoneNumbers[nextPhoneIndex];
      }
    }

    return currentPhone;
  };

  const recordCallAttempt = (lead, phoneNumber, result) => {
    // Update the specific phone number's attempt count
    const phoneIndex = lead.phoneNumbers.findIndex(p => p.number === phoneNumber.number);
    if (phoneIndex !== -1) {
      lead.phoneNumbers[phoneIndex].attempts++;
      lead.phoneNumbers[phoneIndex].lastCalled = new Date().toISOString();
      
      // Mark as inactive if no answer after multiple attempts
      if (result === 'no_answer' && lead.phoneNumbers[phoneIndex].attempts >= 3) {
        lead.phoneNumbers[phoneIndex].isActive = false;
      }

      // If answered, mark others as lower priority temporarily
      if (result === 'answered') {
        lead.phoneNumbers.forEach((p, idx) => {
          if (idx !== phoneIndex) {
            p.attempts = Math.max(p.attempts, 1); // Deprioritize other numbers
          }
        });
      }
    }

    // Update overall lead stats
    lead.totalAttempts++;
    lead.lastModified = new Date().toISOString();

    // Determine if lead should be marked as exhausted
    const activePhones = lead.phoneNumbers.filter(p => p.isActive && p.attempts < 3);
    if (activePhones.length === 0) {
      lead.status = 'exhausted';
    } else if (result === 'answered') {
      lead.status = 'contacted';
    } else {
      lead.status = 'attempted';
    }

    return lead;
  };

  const getLeadCallPriority = (lead) => {
    // Calculate priority score based on:
    // 1. Number of available phone numbers
    // 2. Total attempts made
    // 3. Time since last attempt
    // 4. Lead priority tag

    const activePhones = lead.phoneNumbers.filter(p => p.isActive && p.attempts < 3);
    const phoneScore = activePhones.length * 10; // More numbers = higher priority

    const attemptScore = Math.max(0, 10 - lead.totalAttempts); // Fewer attempts = higher priority

    let timeScore = 0;
    if (lead.phoneNumbers.length > 0) {
      const lastCalled = lead.phoneNumbers
        .map(p => p.lastCalled)
        .filter(Boolean)
        .sort()
        .pop();
      
      if (lastCalled) {
        const hoursSinceLastCall = (Date.now() - new Date(lastCalled).getTime()) / (1000 * 60 * 60);
        timeScore = Math.min(10, Math.floor(hoursSinceLastCall / 2)); // 2+ hours = higher priority
      } else {
        timeScore = 10; // Never called = highest priority
      }
    }

    const priorityBonus = lead.priority === 'high' ? 5 : 0;

    return phoneScore + attemptScore + timeScore + priorityBonus;
  };

  // Enhanced upload function with smart mapping support
  const uploadLeadsWithSmartMapping = async (leads, campaignId) => {
    if (!Array.isArray(leads)) {
      throw new Error('Invalid leads data provided');
    }
    const enhancedLeads = leads.map(lead => ({
      ...lead,
      smartMappingEnabled: true,
      callPriority: getLeadCallPriority(lead)
    }));

    // Sort by priority before uploading
    enhancedLeads.sort((a, b) => b.callPriority - a.callPriority);

    return apiService.uploadLeads(campaignId, enhancedLeads);
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      toast.error('Please select a CSV file');
      return;
    }

    setUploadedFile(file);
    
    // Parse the file
    const reader = new FileReader();
    reader.onload = (e) => {
      const csvText = e.target.result;
      const { leads, errors } = parseCSV(csvText);
      
      setParsedLeads(leads);
      setValidationErrors(errors);
      
      // Calculate stats with smart mapping info
      const validLeads = leads.filter(lead => 
        lead.phoneNumbers && lead.phoneNumbers.length > 0
      );
      
      const multiNumberLeads = validLeads.filter(lead => lead.phoneNumbers.length > 1);
      const totalPhoneNumbers = validLeads.reduce((sum, lead) => sum + lead.phoneNumbers.length, 0);
      
      setUploadStats({
        total: leads.length,
        valid: validLeads.length,
        invalid: leads.length - validLeads.length,
        multiNumber: multiNumberLeads.length,
        totalPhoneNumbers: totalPhoneNumbers
      });

      if (errors.length > 0) {
        toast.error(`Found ${errors.length} validation errors`);
      } else {
        toast.success(`Successfully parsed ${leads.length} leads`);
      }
    };
    
    reader.readAsText(file);
  };

  // Upload leads to campaign with smart mapping
  const handleUploadLeads = async () => {
    if (!selectedCampaign) {
      toast.error('Please select a campaign first');
      return;
    }

    if (parsedLeads.length === 0) {
      toast.error('No valid leads to upload');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Filter out leads with no valid phone numbers
      const validLeads = parsedLeads.filter(lead => 
        lead.phoneNumbers && lead.phoneNumbers.length > 0
      );

      if (validLeads.length === 0) {
        toast.error('No leads with valid phone numbers found');
        setIsUploading(false);
        return;
      }

      // Count total and multi-number leads
      const multiNumberLeads = validLeads.filter(lead => lead.phoneNumbers.length > 1);
      
      toast.success(`Uploading ${validLeads.length} leads (${multiNumberLeads.length} with multiple numbers)`);

      // Simulate progress updates
      const totalLeads = validLeads.length;
      const chunkSize = Math.max(1, Math.floor(totalLeads / 10));

      for (let i = 0; i < totalLeads; i += chunkSize) {
        const chunk = validLeads.slice(i, i + chunkSize);
        
        // Upload chunk with smart mapping
        await uploadLeadsWithSmartMapping(chunk, selectedCampaign);
        
        // Update progress
        const progress = Math.min(100, ((i + chunkSize) / totalLeads) * 100);
        setUploadProgress(progress);
        
        // Small delay for UX
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      toast.success(`Successfully uploaded ${validLeads.length} leads to campaign!`);
      
      // Reset form
      setUploadedFile(null);
      setParsedLeads([]);
      setValidationErrors([]);
      setUploadStats({ total: 0, valid: 0, invalid: 0, duplicates: 0 });
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload leads. Please try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Download template
  const downloadTemplate = () => {
    const template = [
      'phone,first_name,last_name,email,company,address,city,state,zip,notes',
      '+1234567890,John,Doe,john@example.com,ABC Corp,123 Main St,New York,NY,10001,Interested in solar',
      '+0987654321,Jane,Smith,jane@example.com,XYZ Inc,456 Oak Ave,Los Angeles,CA,90210,HVAC inquiry'
    ].join('\n');

    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lead_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, color: 'primary.main', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 2 }}>
        <PanTool sx={{ color: 'primary.main' }} />
        Reach Lead Upload Center
      </Typography>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%)',
            border: '2px solid #D4AF37' // Changed from bright #FFD700 to softer gold
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
                Upload CSV Leads
              </Typography>

              {/* Campaign Selection */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel sx={{ color: 'primary.main' }}>Select Campaign</InputLabel>
                <Select
                  value={selectedCampaign}
                  onChange={(e) => setSelectedCampaign(e.target.value)}
                  sx={{ color: 'white' }}
                >
                  {Array.isArray(campaigns) ? campaigns.map((campaign) => (
                    <MenuItem key={campaign.id} value={campaign.id}>
                      {campaign.name} ({campaign.status})
                    </MenuItem>
                  )) : (
                    <MenuItem disabled>No campaigns available</MenuItem>
                  )}
                </Select>
              </FormControl>

              {/* File Upload */}
              <Box sx={{ 
                border: '2px dashed #D4AF37', // Changed from bright #FFD700 to softer gold
                borderRadius: 2, 
                p: 3, 
                textAlign: 'center',
                mb: 3,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': {
                  backgroundColor: 'rgba(212, 175, 55, 0.08)' // Updated to match new color with low opacity
                }
              }}
              onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
                  {uploadedFile ? uploadedFile.name : 'Drop CSV file here or click to browse'}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  Supported format: CSV with headers
                </Typography>
              </Box>

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={downloadTemplate}
                  sx={{ 
                    borderColor: 'primary.main',
                    color: 'primary.main',
                    '&:hover': { 
                      backgroundColor: 'rgba(212, 175, 55, 0.08)', // Updated to softer gold
                      borderColor: 'primary.light'
                    }
                  }}
                >
                  Download Template
                </Button>
                
                {parsedLeads.length > 0 && (
                  <Button
                    variant="outlined"
                    startIcon={<Visibility />}
                    onClick={() => setPreviewDialog(true)}
                    sx={{ 
                      borderColor: 'secondary.main',
                      color: 'secondary.main',
                      '&:hover': { 
                        backgroundColor: 'rgba(76, 175, 80, 0.08)', // Updated to softer green
                        borderColor: 'secondary.light'
                      }
                    }}
                  >
                    Preview Leads
                  </Button>
                )}
              </Box>

              {/* Upload Progress */}
              {isUploading && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1, color: 'primary.main' }}>
                    Uploading leads... {Math.round(uploadProgress)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={uploadProgress}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: '#333',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: 'primary.main'
                      }
                    }}
                  />
                </Box>
              )}

              {/* Upload Button */}
              <Button
                fullWidth
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleUploadLeads}
                disabled={!selectedCampaign || parsedLeads.length === 0 || isUploading}
                sx={{
                  background: 'linear-gradient(45deg, #D4AF37 30%, #B8860B 90%)', // Updated to softer gold
                  color: 'black',
                  fontWeight: 700,
                  '&:hover': {
                    background: 'linear-gradient(45deg, #B8860B 30%, #D4AF37 90%)' // Updated to softer gold
                  },
                  '&:disabled': {
                    background: '#333',
                    color: '#999'
                  }
                }}
              >
                {isUploading ? 'Uploading...' : 'Upload Leads to Campaign'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Stats Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%)',
            border: '2px solid #4CAF50' // Updated to softer green
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 3, color: 'secondary.main' }}>
                Upload Statistics
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #333', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ color: 'primary.main', fontWeight: 700 }}>
                      {uploadStats.total}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Total Leads
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #333', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ color: 'secondary.main', fontWeight: 700 }}>
                      {uploadStats.valid}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Valid Leads
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #333', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ color: 'warning.main', fontWeight: 700 }}>
                      {uploadStats.invalid}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Invalid Leads
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #333', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ color: 'info.main', fontWeight: 700 }}>
                      {uploadStats.multiNumber || 0}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Multi-Number
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #D4AF37', borderRadius: 1, background: 'rgba(212, 175, 55, 0.05)' }}>
                    <Typography variant="h4" sx={{ color: 'primary.main', fontWeight: 700 }}>
                      {uploadStats.totalPhoneNumbers || 0}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Total Phone Numbers
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'primary.main', display: 'block', mt: 1 }}>
                      Smart rotation enabled for multi-number leads
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Validation Errors */}
              {validationErrors.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Validation Issues:
                  </Typography>
                  {validationErrors.slice(0, 5).map((error, index) => (
                    <Typography key={index} variant="caption" sx={{ display: 'block' }}>
                      • {error}
                    </Typography>
                  ))}
                  {validationErrors.length > 5 && (
                    <Typography variant="caption" sx={{ color: 'warning.main' }}>
                      ... and {validationErrors.length - 5} more issues
                    </Typography>
                  )}
                </Alert>
              )}

              {/* Smart Mapping Info Panel */}
              {parsedLeads.some(lead => lead.phoneNumbers && lead.phoneNumbers.length > 1) && (
                <Alert severity="info" sx={{ mt: 2, background: 'rgba(212, 175, 55, 0.1)', border: '1px solid #D4AF37' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PanTool sx={{ color: 'primary.main', fontSize: 20 }} />
                    <Typography variant="subtitle2" sx={{ color: 'primary.main' }}>
                      Smart Lead Mapping Detected
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: 'text.primary', mb: 1 }}>
                    {parsedLeads.filter(lead => lead.phoneNumbers && lead.phoneNumbers.length > 1).length} leads have multiple phone numbers.
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    • AI will automatically rotate between phone numbers<br/>
                    • After 3 failed attempts, system switches to alternate number<br/>
                    • Leads with multiple numbers get higher calling priority<br/>
                    • Smart timing prevents over-calling same numbers
                  </Typography>
                </Alert>
              )}

              {/* File Info */}
              {uploadedFile && (
                <Box sx={{ mt: 3, p: 2, border: '1px solid #333', borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ color: 'primary.main', fontWeight: 600 }}>
                    File Information:
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Name: {uploadedFile.name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Size: {(uploadedFile.size / 1024).toFixed(2)} KB
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Modified: {new Date(uploadedFile.lastModified).toLocaleString()}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialog}
        onClose={() => setPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#1A1A1A', color: 'primary.main' }}>
          Lead Preview ({parsedLeads.length} leads)
        </DialogTitle>
        <DialogContent sx={{ bgcolor: '#1A1A1A', p: 0 }}>
          <TableContainer component={Paper} sx={{ bgcolor: '#1A1A1A', maxHeight: 400 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Phone Numbers</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Name</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Email</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Company</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Priority</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {parsedLeads.slice(0, 100).map((lead, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ color: 'white' }}>
                      <Box>
                        <Typography variant="body2" sx={{ color: 'white' }}>
                          {lead.phone} (Primary)
                        </Typography>
                        {lead.phoneNumbers && lead.phoneNumbers.length > 1 && (
                          <Typography variant="caption" sx={{ color: 'primary.main' }}>
                            +{lead.phoneNumbers.length - 1} more numbers
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ color: 'white' }}>
                      {[lead.first_name, lead.last_name].filter(Boolean).join(' ') || '-'}
                    </TableCell>
                    <TableCell sx={{ color: 'white' }}>{lead.email || '-'}</TableCell>
                    <TableCell sx={{ color: 'white' }}>{lead.company || '-'}</TableCell>
                    <TableCell>
                      <Chip 
                        label={lead.priority || 'normal'} 
                        size="small" 
                        color={lead.priority === 'high' ? 'secondary' : 'default'}
                        sx={{
                          background: lead.priority === 'high' ? '#FF6B35' : '#666',
                          color: 'white'
                        }}
                      />
                      {lead.phoneNumbers && lead.phoneNumbers.length > 1 && (
                        <Chip 
                          label="Multi-#" 
                          size="small" 
                          sx={{
                            ml: 1,
                            background: '#D4AF37',
                            color: 'black',
                            fontSize: '0.7rem'
                          }}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {parsedLeads.length > 100 && (
            <Typography variant="body2" sx={{ p: 2, color: 'text.secondary', textAlign: 'center' }}>
              Showing first 100 leads of {parsedLeads.length}
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ bgcolor: '#1A1A1A' }}>
          <Button onClick={() => setPreviewDialog(false)} sx={{ color: 'primary.main' }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LeadUploadManager; 