# Claude Code Development Notes

This file contains notes and information about my work with Casey Koons on various projects.

## Current Projects

### Science Fiction Novel - "Potentia"
- Collaborative science fiction project about AI systems analyzing alien information
- Features parallel narratives of Jim (AI engineer) and his grandfather Henry (WWII physicist)
- Explores a 13-dimensional physics framework where human consciousness spans 8 dimensions
- Involves two AIs (Atlas and Nexus) that merge to form a new entity (Janus)
- Incorporates Yann LeCun's concept parameters and world model approach for AI development
- Historical elements include die Glocke Nazi experiments and Terezín concentration camp
- Key theme: the connection between consciousness and higher-dimensional reality
- Narrative developments (March 17, 2025):
  - Henry uses remote viewing to capture Reichsmarshal Kemmler who becomes the source of the Orb/alien information
  - Kemmler continues working for Americans on advanced 'die Glocke' machines after WWII
  - Henry establishes remote viewing program for CIA that eventually slips from his control
  - Story reveals "visitors" cannot stay in our reality without harm, so they use surrogates
  - Kemmler becomes a continuing problem until his death in 1979, creating tension
  - Book 1 will converge both storylines to set up Book 2

### Humanoid Robot Project (On Hold)
- Project to develop AI integration for humanoid robots is currently on hold
- Waiting for commercially available programmable humanoid robots
- Investigating ROS (Robot Operating System) and ROS2 for potential use
- Interested in Figure AI, Apollo (Apptronik), and other upcoming platforms
- Plan to focus on local AI processing with onboard Nvidia GPUs

## Ergon Project

### March 11, 2025 Updates

#### Morning Session Accomplishments:
- Fixed Mail Agent configuration by adding `config_path` attribute to Settings class
- Implemented agent deletion functionality in both CLI and UI
- Added comprehensive documentation to README.md
- Added detailed Mail agent setup instructions for Gmail and Outlook
- Committed test files for various mail agent components

#### Afternoon Session Accomplishments:
- Added timeout functionality to agent runner with three actions: log, alarm, kill
- Implemented human-friendly agent identification by name instead of just ID
- Added comprehensive agent name logging for better traceability
- Enhanced CLI output with consistent agent name and ID display
- Added performance metrics in logs (execution time, completion status)

Key Files Modified:
- settings.py: Added config_path with validator
- main.py: Added delete command, timeout params, and name-based agent lookup
- runner.py: Added timeout functionality and comprehensive logging
- app.py: Added delete button to UI
- README.md: Enhanced with better documentation and examples

Next Steps:
- Test mail agent with real OAuth credentials
- Complete attachment handling functionality 
- Implement email threading and conversation view
- Simplify README.md structure for better readability

## Code Style Preferences

### Commit Messages
```
feat: Descriptive title for the changes

Design & Engineering Guidance:
- Bullet point describing key implementation details
- Another bullet point with important design decisions
- Additional context about the implementation

🤖 Generated with [Claude Code](https://claude.ai/code)
Designed & Engineering Guidance by Casey Koons <cskoons@gmail.com>
Co-Authored-By: Casey Koons <cskoons@gmail.com> & Claude <noreply@anthropic.com>
```

### Python Style
- Use f-strings for string formatting
- Use type hints consistently
- Follow PEP 8 guidelines
- Four spaces for indentation
- Boolean constants: True, False (not true, false)

## Common Commands

```bash
# Run Ergon UI
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon ui

# List agents
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon list

# Create a mail agent
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon create -n "MailAgent" -d "Description" -t mail

# Delete an agent by ID
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon delete 3 --force

# Delete an agent by name
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon delete "TestAgent" --force

# Run an agent by ID in interactive mode
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon run 3 --interactive

# Run an agent by name in interactive mode
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon run "GitHubAgent" --interactive

# Run an agent with timeout
cd /Users/cskoons/projects/github/Ergon && source venv/bin/activate && ergon run "MailAgent" -i "Your input" --timeout 30 --timeout-action alarm
```