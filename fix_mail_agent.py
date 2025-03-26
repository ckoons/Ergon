import os
import sys
import json
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

# Add the current directory to the path so we can import from the ergon package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ergon.core.database.engine import get_db_session
from ergon.core.database.models import Agent, AgentTool, AgentFile

def fix_mail_agent():
    """Fix the mail agent by adding a 'type' column to the agent model."""
    
    print("Finding mail agents in the database...")
    with get_db_session() as db:
        # Find mail agents by name or ID
        mail_agents = []
        
        # Look for agents with name containing "Mail"
        name_matches = db.query(Agent).filter(Agent.name.like('%Mail%')).all()
        if name_matches:
            mail_agents.extend(name_matches)
            for agent in name_matches:
                print(f"Found mail agent by name: {agent.name} (ID: {agent.id})")
        
        # Add specific agent ID if we know it (from the previous listing, ID = 4)
        specific_agent = db.query(Agent).filter(Agent.id == 4).first()
        if specific_agent and specific_agent not in mail_agents:
            mail_agents.append(specific_agent)
            print(f"Found mail agent by ID: {specific_agent.name} (ID: {specific_agent.id})")
        
        # Also try to find agents with mail-related tools
        all_agents = db.query(Agent).all()
        for agent in all_agents:
            if agent in mail_agents:
                continue  # Skip if already added
                
            # Check if agent has mail tools
            tools = db.query(AgentTool).filter(AgentTool.agent_id == agent.id).all()
            tool_names = [tool.name for tool in tools]
            
            if any(name.startswith("mail_") for name in tool_names) or any("email" in name.lower() for name in tool_names):
                mail_agents.append(agent)
                print(f"Found mail agent by tools: {agent.name} (ID: {agent.id})")
        
        if not mail_agents:
            print("No mail agents found.")
            return
        
        print("\nFixing mail agents...")
        # Add metadata to each mail agent with type='mail'
        for agent in mail_agents:
            print(f"Adding type to agent: {agent.name} (ID: {agent.id})")
            
            # Check if agent has existing metadata
            metadata_file = db.query(AgentFile).filter(
                AgentFile.agent_id == agent.id,
                AgentFile.filename == 'metadata.json'
            ).first()
            
            if metadata_file:
                try:
                    metadata = json.loads(metadata_file.content)
                    metadata['type'] = 'mail'
                    metadata_file.content = json.dumps(metadata)
                    print(f"Updated existing metadata for agent {agent.name}")
                except json.JSONDecodeError:
                    metadata_file.content = json.dumps({'type': 'mail'})
                    print(f"Replaced invalid metadata for agent {agent.name}")
            else:
                # Create new metadata file
                new_file = AgentFile(
                    agent_id=agent.id,
                    filename='metadata.json',
                    file_type='application/json',
                    content=json.dumps({'type': 'mail'})
                )
                db.add(new_file)
                print(f"Created new metadata file for agent {agent.name}")
            
            db.commit()
            print(f"Successfully fixed agent {agent.name} (ID: {agent.id})")
        
        print("\nFix complete. Mail agents should now work correctly.")


if __name__ == "__main__":
    fix_mail_agent()