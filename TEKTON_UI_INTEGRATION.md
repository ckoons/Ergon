# Tekton UI Integration Guide for Ergon

This guide explains how to integrate Ergon with the Tekton UI framework.

## Overview

Ergon has been adapted to work within the Tekton UI framework, which provides:

- A consistent title area across all components
- A left panel for navigation
- A right panel for component-specific interfaces
- A unified look and feel

## Integration Components

### 1. UI Connector (`ui_connector.js`)

The connector exports:

- Tab-specific components (Console, Data, Visualization, Settings)
- `componentInfo` - Metadata for Tekton to identify and configure the component
- `ErgonTabs` - Object containing all the tab components for direct import

### 2. Tab Components

The UI connector now implements four specific tabs for the right panel:

1. **Console Tab (`ErgonConsoleTab`)**
   - Agent listing and management
   - Create, delete, and run agents
   - Status indicators for each agent

2. **Data Tab (`ErgonDataTab`)**
   - Agent data visualization
   - Execution history
   - Result inspection

3. **Visualization Tab (`ErgonVisualizationTab`)**
   - Performance metrics
   - Usage statistics
   - Analytics dashboards

4. **Settings Tab (`ErgonSettingsTab`)**
   - Agent default configurations
   - API key management
   - System preferences

### 3. API Services

The integration uses two service layers:

1. **API Service (`ApiService.js`)**
   - REST API communication with Ergon backend
   - CRUD operations for agents
   - Settings management

2. **WebSocket Service (`WebSocketService.js`)**
   - Real-time updates for agent status
   - Live output streaming
   - Event subscription system

## Adding Ergon to Tekton

1. Register the component in Tekton's component manager:

```javascript
// In component_manager.py
mock_components = [
    // Other components...
    {
        "id": "ergon",
        "name": "Ergon",
        "status": "READY",
        "description": "Agent Builder",
        "version": "0.9.0"
    }
]
```

2. Ensure Ergon's UI connector is properly implemented:

```javascript
// ui_connector.js
export const componentInfo = {
  name: 'Ergon',
  description: 'Intelligent Agent and Workflow Manager',
  version: '1.0.0',
  specialties: ['Agents', 'Memory', 'Workflow'],
  tabs: {
    console: {
      label: 'Console',
      component: ErgonConsoleTab
    },
    data: {
      label: 'Data',
      component: ErgonDataTab
    },
    visualization: {
      label: 'Visualization',
      component: ErgonVisualizationTab
    },
    settings: {
      label: 'Settings',
      component: ErgonSettingsTab
    }
  }
};
```

3. Start the Tekton UI:

```bash
cd /Users/cskoons/projects/github/Tekton
./hephaestus_launch
```

## Material UI Integration

The Ergon UI components use Material UI to match the Tekton design system:

- `Box` for layout containers
- `Typography` for consistent text styling
- `Paper` for card-like containers
- `Button` for actions
- `List` and `ListItem` for agent listings
- `Chip` for status indicators
- `TextField` for form inputs

All components are designed to be responsive and adapt to the right panel's dimensions.

## Component Communication

The tabs access the Ergon backend through:

1. **REST API Endpoints**
   - `/api/ergon/agents` - Agent CRUD operations
   - `/api/ergon/agent-types` - Available agent types
   - `/api/ergon/settings` - System settings

2. **WebSocket Events**
   - `agent_status` - Agent status updates
   - `agent_output` - Live output from running agents
   - `settings_changed` - Settings update notifications

## Styling Guidelines

- Ergon uses its brand color (`#f97316` - orange) for accents
- Form elements follow Material UI patterns
- List items use consistent layouts
- Cards have subtle shadows for elevation
- Status indicators use semantic colors (green for ready, red for errors)

## Customization

To add more Ergon functionality:

1. Create a new tab component in `ui_connector.js`
2. Add corresponding API services in `ApiService.js`
3. Register the new tab in the `componentInfo.tabs` object
4. Update the `ErgonTabs` export to include the new component

## Troubleshooting

If the Ergon UI fails to load:

1. Check browser console for JavaScript errors
2. Verify that Ergon appears in the component list from the API
3. Ensure the UI connector is properly structured
4. Check that the TabPanel components in ComponentView.js are working properly

## Testing

You can test the Ergon UI integration by:

1. Navigating to the Ergon component in the Tekton UI
2. Checking that all tabs are accessible and responsive
3. Verifying that mock data appears in the agent list
4. Confirming that the UI elements match the Tekton design system

For more details on the CLI wrapping, see the `README_INTEGRATION.md` file.