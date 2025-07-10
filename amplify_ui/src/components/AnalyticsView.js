import React from 'react';
import { Typography, Box } from '@mui/material';

function AnalyticsView() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: 'primary.main', fontWeight: 700 }}>
        Elite Analytics Center
      </Typography>
      <Typography variant="body1" sx={{ color: 'text.secondary' }}>
        Advanced analytics dashboard coming soon...
      </Typography>
    </Box>
  );
}

export default AnalyticsView; 