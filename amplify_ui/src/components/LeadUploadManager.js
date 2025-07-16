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

  // CSV parsing function
  const parseCSV = (csvText) => {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    // Expected headers (flexible mapping)
    const headerMap = {
      'phone': ['phone', 'phone_number', 'phonenumber', 'mobile', 'cell'],
      'first_name': ['first_name', 'firstname', 'fname', 'first'],
      'last_name': ['last_name', 'lastname', 'lname', 'last'],
      'email': ['email', 'email_address', 'emailaddress'],
      'company': ['company', 'business', 'organization'],
      'address': ['address', 'street', 'location'],
      'city': ['city'],
      'state': ['state', 'province'],
      'zip': ['zip', 'zipcode', 'postal', 'postalcode'],
      'notes': ['notes', 'comments', 'description']
    };

    // Find column indices
    const columnMap = {};
    Object.keys(headerMap).forEach(key => {
      const matchingHeader = headers.find(h => headerMap[key].includes(h));
      if (matchingHeader) {
        columnMap[key] = headers.indexOf(matchingHeader);
      }
    });

    // Parse rows
    const leads = [];
    const errors = [];
    
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === '') continue;
      
      const cells = lines[i].split(',').map(c => c.trim());
      const lead = {};
      
      // Extract data based on column mapping
      Object.keys(columnMap).forEach(key => {
        if (columnMap[key] !== undefined && cells[columnMap[key]]) {
          lead[key] = cells[columnMap[key]].replace(/"/g, '');
        }
      });

      // Validation
      if (!lead.phone) {
        errors.push(`Row ${i + 1}: Missing phone number`);
      } else if (!/^\+?[\d\s\-\(\)]{10,}$/.test(lead.phone)) {
        errors.push(`Row ${i + 1}: Invalid phone number format`);
      }

      if (lead.email && !/\S+@\S+\.\S+/.test(lead.email)) {
        errors.push(`Row ${i + 1}: Invalid email format`);
      }

      // Add metadata
      lead.id = `lead_${Date.now()}_${i}`;
      lead.status = 'new';
      lead.created_at = new Date().toISOString();

      leads.push(lead);
    }

    return { leads, errors };
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
      
      // Calculate stats
      const validLeads = leads.filter(lead => 
        lead.phone && /^\+?[\d\s\-\(\)]{10,}$/.test(lead.phone)
      );
      
      setUploadStats({
        total: leads.length,
        valid: validLeads.length,
        invalid: leads.length - validLeads.length,
        duplicates: 0 // TODO: Implement duplicate detection
      });

      if (errors.length > 0) {
        toast.error(`Found ${errors.length} validation errors`);
      } else {
        toast.success(`Successfully parsed ${leads.length} leads`);
      }
    };
    
    reader.readAsText(file);
  };

  // Upload leads to campaign
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
      // Filter out invalid leads
      const validLeads = parsedLeads.filter(lead => 
        lead.phone && /^\+?[\d\s\-\(\)]{10,}$/.test(lead.phone)
      );

      // Simulate progress updates
      const totalLeads = validLeads.length;
      const chunkSize = Math.max(1, Math.floor(totalLeads / 10));

      for (let i = 0; i < totalLeads; i += chunkSize) {
        const chunk = validLeads.slice(i, i + chunkSize);
        
        // Upload chunk
        await apiService.uploadLeads(selectedCampaign, chunk);
        
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
            border: '2px solid #FFD700'
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
                  {campaigns?.map((campaign) => (
                    <MenuItem key={campaign.id} value={campaign.id}>
                      {campaign.name} ({campaign.status})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* File Upload */}
              <Box sx={{ 
                border: '2px dashed #FFD700', 
                borderRadius: 2, 
                p: 3, 
                textAlign: 'center',
                mb: 3,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': {
                  backgroundColor: 'rgba(255, 215, 0, 0.1)'
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
                      backgroundColor: 'rgba(255, 215, 0, 0.1)',
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
                        backgroundColor: 'rgba(0, 200, 81, 0.1)',
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
                  background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)',
                  color: 'black',
                  fontWeight: 700,
                  '&:hover': {
                    background: 'linear-gradient(45deg, #FFA000 30%, #FFD700 90%)'
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
            border: '2px solid #00C851'
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
                      {uploadStats.duplicates}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Duplicates
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Validation Errors */}
              {validationErrors.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      Found {validationErrors.length} validation errors:
                    </Typography>
                  </Alert>
                  <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                    {validationErrors.slice(0, 10).map((error, index) => (
                      <Typography key={index} variant="body2" sx={{ color: 'warning.main', mb: 0.5 }}>
                        • {error}
                      </Typography>
                    ))}
                    {validationErrors.length > 10 && (
                      <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1 }}>
                        ... and {validationErrors.length - 10} more errors
                      </Typography>
                    )}
                  </Box>
                </Box>
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
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Phone</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Name</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Email</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Company</TableCell>
                  <TableCell sx={{ color: 'primary.main', fontWeight: 600 }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {parsedLeads.slice(0, 100).map((lead, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ color: 'white' }}>{lead.phone}</TableCell>
                    <TableCell sx={{ color: 'white' }}>
                      {[lead.first_name, lead.last_name].filter(Boolean).join(' ') || '-'}
                    </TableCell>
                    <TableCell sx={{ color: 'white' }}>{lead.email || '-'}</TableCell>
                    <TableCell sx={{ color: 'white' }}>{lead.company || '-'}</TableCell>
                    <TableCell>
                      <Chip 
                        label={lead.status} 
                        size="small" 
                        color={lead.phone && /^\+?[\d\s\-\(\)]{10,}$/.test(lead.phone) ? 'success' : 'error'}
                      />
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