#!/usr/bin/env python3
"""
Simple GitHub API demonstration using PyGithub directly.
"""

import os
import json
from github import Github, GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main function to demonstrate GitHub API interactions."""
    # Get GitHub API token from environment
    github_token = os.getenv("GITHUB_API_TOKEN")
    if not github_token:
        print("Error: GitHub API token not found. Please set the GITHUB_API_TOKEN environment variable.")
        return

    # Initialize PyGithub client
    g = Github(github_token)
    
    try:
        # Get the authenticated user
        user = g.get_user()
        print(f"Authenticated as: {user.login}")
        
        # List repositories
        print("\nYour repositories:")
        for repo in user.get_repos():
            print(f"- {repo.name} ({repo.html_url})")
            
        # List recent activity
        print("\nRecent events:")
        for event in user.get_events()[:5]:
            print(f"- {event.type} at {event.created_at}")
    
    except GithubException as e:
        print(f"GitHub API Error: {e.status} - {e.data.get('message')}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()