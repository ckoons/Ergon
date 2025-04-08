// Ergon UI Connector for Tekton Platform
// This file defines a simple connector for displaying Ergon content in the Tekton UI
// IMPORTANT: This connector ONLY displays content in the existing panel structure

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Chip
} from '@mui/material';

import SmartToyIcon from '@mui/icons-material/SmartToy';

// Simple component for displaying in the right panel
const ErgonComponent = () => {
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Ergon Agent Management</Typography>
      
      <Paper sx={{ flexGrow: 1, p: 2, overflow: 'auto' }}>
        <List>
          <ListItem>
            <ListItemIcon>
              <SmartToyIcon sx={{ color: '#f97316' }} />
            </ListItemIcon>
            <ListItemText 
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  GitHubAgent
                  <Chip 
                    label="github"
                    size="small"
                    sx={{ ml: 1, bgcolor: '#f97316', color: 'white', fontSize: '0.7rem' }}
                  />
                </Box>
              } 
              secondary="Monitors GitHub repositories"
            />
          </ListItem>
          <Divider />
          
          <ListItem>
            <ListItemIcon>
              <SmartToyIcon sx={{ color: '#f97316' }} />
            </ListItemIcon>
            <ListItemText 
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  MailAgent
                  <Chip 
                    label="mail"
                    size="small"
                    sx={{ ml: 1, bgcolor: '#f97316', color: 'white', fontSize: '0.7rem' }}
                  />
                </Box>
              } 
              secondary="Processes email communications"
            />
          </ListItem>
          <Divider />
          
          <ListItem>
            <ListItemIcon>
              <SmartToyIcon sx={{ color: '#f97316' }} />
            </ListItemIcon>
            <ListItemText 
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  BrowserAgent
                  <Chip 
                    label="browser"
                    size="small"
                    sx={{ ml: 1, bgcolor: '#f97316', color: 'white', fontSize: '0.7rem' }}
                  />
                </Box>
              } 
              secondary="Web browsing and research"
            />
          </ListItem>
        </List>
      </Paper>
    </Box>
  );
};

// Main component info export - keeps it extremely simple
export default {
  id: "ergon",
  name: "Ergon",
  description: "Agent Builder",
  version: "0.9.0",
  component: ErgonComponent
};