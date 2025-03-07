#!/usr/bin/env python3
"""
Simple GitHub agent that can be used directly or from Agenteer.
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional, Union
import logging
from github import Github, GithubException, BadCredentialsException, UnknownObjectException
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class GitHubAgent:
    """
    GitHub Agent that can create, delete and manage repositories,
    as well as issues, pull requests, and other GitHub operations.
    """
    
    def __init__(self, token=None):
        """Initialize the GitHub agent."""
        logger.info("Initializing GitHub agent")
        
        # Load environment variables
        load_dotenv()
        
        # Get GitHub API token
        self.token = token or os.getenv("GITHUB_API_TOKEN")
        if not self.token:
            raise ValueError("GitHub API token not found. Please set the GITHUB_API_TOKEN environment variable.")
        
        # Initialize PyGithub client
        self.client = Github(self.token)
        
        # Get the authenticated user
        self.user = self.client.get_user()
        logger.info(f"Authenticated as: {self.user.login}")
    
    def process_request(self, request: str) -> str:
        """
        Process a user request and execute the appropriate GitHub operation.
        
        Args:
            request: User request string
            
        Returns:
            Response from the GitHub API or error message
        """
        request = request.lower().strip()
        
        try:
            # List repositories
            if any(phrase in request for phrase in ["list repositories", "list repos", "list my repos", "list my repositories", "show repositories", "show repos"]):
                return self.list_repositories(request)
                
            # Create repository
            elif any(phrase in request for phrase in ["create repository", "create repo", "create a repository", "create a repo", "make repository", "make repo", "new repository", "new repo"]):
                return self.create_repository(request)
                
            # Delete repository
            elif any(phrase in request for phrase in ["delete repository", "delete repo", "remove repository", "remove repo"]):
                return self.delete_repository(request)
                
            # Get repository by name (specific case)
            elif "show repository" in request or "show repo" in request or "get repository" in request or "get repo" in request:
                return self.get_repository(request)
                
            # Create issue
            elif "create issue" in request:
                return self.create_issue(request)
                
            # List issues
            elif "list issues" in request:
                return self.list_issues(request)
                
            # Create pull request
            elif any(phrase in request for phrase in ["create pull request", "create pr", "make pull request", "make pr"]):
                return self.create_pull_request(request)
                
            # List branches
            elif "list branches" in request:
                return self.list_branches(request)
                
            # Unknown request
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Unknown GitHub request. Try one of these: list repositories, create repository, delete repository, get repository, create issue, list issues, create pull request, list branches"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }, indent=2)
    
    def list_repositories(self, request: str) -> str:
        """List repositories for the authenticated user."""
        try:
            # Determine optional filters
            visibility = "all"
            if "public" in request:
                visibility = "public"
            elif "private" in request:
                visibility = "private"
                
            sort = "updated"
            if "created" in request:
                sort = "created"
            elif "pushed" in request:
                sort = "pushed"
            elif "name" in request:
                sort = "full_name"
            
            # Get repositories
            repos = self.user.get_repos(visibility=visibility, sort=sort)
            
            # Convert to list
            repo_list = []
            for repo in repos:
                repo_list.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "private": repo.private,
                    "language": repo.language,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                })
            
            return json.dumps({
                "status": "success",
                "count": len(repo_list),
                "repositories": repo_list
            }, indent=2)
        
        except Exception as e:
            logger.error(f"Error listing repositories: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error listing repositories: {str(e)}"
            }, indent=2)
    
    def create_repository(self, request: str) -> str:
        """Create a new repository."""
        try:
            # Extract repository name
            name = None
            for phrase in ["named ", "called ", "name ", "named:", "called:", "name:"]:
                if phrase in request:
                    parts = request.split(phrase, 1)
                    if len(parts) > 1:
                        name = parts[1].split()[0].strip()
                        name = name.strip('.,;:"\'()[]{}')
                        break
            
            if not name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository name not specified. Please include 'named [repo_name]' in your request."
                }, indent=2)
            
            # Extract description
            description = None
            if "description" in request:
                parts = request.split("description", 1)
                if len(parts) > 1:
                    description = parts[1].lstrip(": ").split(".")[0].strip()
            
            # Check if private
            private = "private" in request
            
            # Create repository
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True
            )
            
            return json.dumps({
                "status": "success",
                "message": f"Repository {repo.name} created successfully",
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "private": repo.private,
                    "clone_url": repo.clone_url
                }
            }, indent=2)
            
        except GithubException as e:
            logger.error(f"GitHub error creating repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"GitHub error creating repository: {e.data.get('message', str(e))}"
            }, indent=2)
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error creating repository: {str(e)}"
            }, indent=2)
    
    def delete_repository(self, request: str) -> str:
        """Delete a repository."""
        try:
            # For delete, we want to use specific patterns to find the repo name
            repo_name = None
                
            # Look for specific phrases
            for phrase in ["named ", "called ", "name ", "repo ", "named:", "called:", "name:", "repo:"]:
                if phrase in request:
                    parts = request.split(phrase, 1)
                    if len(parts) > 1:
                        repo_name = parts[1].split()[0].strip()
                        repo_name = repo_name.strip('.,;:"\'()[]{}')
                        break
            
            if not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository name not specified. Please specify the repository name."
                }, indent=2)
            
            # Check if repo_name includes username
            if '/' in repo_name:
                username, repo = repo_name.split('/')
                if username != self.user.login:
                    return json.dumps({
                        "status": "error",
                        "message": f"You can only delete your own repositories. Got {username} but authenticated as {self.user.login}"
                    }, indent=2)
                repo_name = repo
            
            # Get repository
            repo = self.user.get_repo(repo_name)
            
            # Confirmation (this would be interactive in a real agent)
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url
            }
            
            # In a real agent, we would ask for confirmation here
            # For demo purposes, we'll just delete it directly if "confirm" is in the request
            if "confirm" in request or "yes" in request or "force" in request:
                repo.delete()
                return json.dumps({
                    "status": "success",
                    "message": f"Repository {repo_name} deleted successfully"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "warning",
                    "message": f"Repository {repo_name} found. To confirm deletion, include 'confirm' in your request.",
                    "repository": repo_info
                }, indent=2)
            
        except UnknownObjectException:
            return json.dumps({
                "status": "error",
                "message": f"Repository {repo_name} not found"
            }, indent=2)
        except GithubException as e:
            logger.error(f"GitHub error deleting repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"GitHub error deleting repository: {e.data.get('message', str(e))}"
            }, indent=2)
        except Exception as e:
            logger.error(f"Error deleting repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error deleting repository: {str(e)}"
            }, indent=2)
    
    def get_repository(self, request: str) -> str:
        """Get details of a repository."""
        try:
            # Extract repository name
            # First, try to get the last word in the request if it's short
            words = request.split()
            if len(words) > 0:
                repo_name = words[-1].strip('.,;:"\'()[]{}')
            else:
                repo_name = None
                
            # If that doesn't look right, try more specific patterns
            if not repo_name or len(repo_name) < 3 or repo_name in ["repo", "repository"]:
                repo_name = None
                for phrase in ["named ", "called ", "name ", "repo ", "named:", "called:", "name:", "repo:"]:
                    if phrase in request:
                        parts = request.split(phrase, 1)
                        if len(parts) > 1:
                            repo_name = parts[1].split()[0].strip()
                            repo_name = repo_name.strip('.,;:"\'()[]{}')
                            break
            
            if not repo_name:
                return json.dumps({
                    "status": "error",
                    "message": "Repository name not specified. Please specify the repository name."
                }, indent=2)
            
            # Check if repo_name includes username
            if '/' not in repo_name:
                repo_name = f"{self.user.login}/{repo_name}"
            
            # Get repository
            repo = self.client.get_repo(repo_name)
            
            # Return repository details
            return json.dumps({
                "status": "success",
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "owner": repo.owner.login,
                    "description": repo.description,
                    "url": repo.html_url,
                    "private": repo.private,
                    "fork": repo.fork,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "language": repo.language,
                    "default_branch": repo.default_branch,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": repo.open_issues_count,
                    "clone_url": repo.clone_url
                }
            }, indent=2)
            
        except UnknownObjectException:
            return json.dumps({
                "status": "error",
                "message": f"Repository {repo_name} not found"
            }, indent=2)
        except GithubException as e:
            logger.error(f"GitHub error getting repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"GitHub error getting repository: {e.data.get('message', str(e))}"
            }, indent=2)
        except Exception as e:
            logger.error(f"Error getting repository: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"Error getting repository: {str(e)}"
            }, indent=2)
    
    def create_issue(self, request: str) -> str:
        """Create a new issue in a repository."""
        # Implementation would go here
        return json.dumps({
            "status": "not_implemented",
            "message": "Create issue functionality not implemented in this demo"
        }, indent=2)
    
    def list_issues(self, request: str) -> str:
        """List issues from a repository."""
        # Implementation would go here
        return json.dumps({
            "status": "not_implemented",
            "message": "List issues functionality not implemented in this demo"
        }, indent=2)
    
    def create_pull_request(self, request: str) -> str:
        """Create a pull request in a repository."""
        # Implementation would go here
        return json.dumps({
            "status": "not_implemented",
            "message": "Create pull request functionality not implemented in this demo"
        }, indent=2)
    
    def list_branches(self, request: str) -> str:
        """List branches in a repository."""
        # Implementation would go here
        return json.dumps({
            "status": "not_implemented",
            "message": "List branches functionality not implemented in this demo"
        }, indent=2)


def main():
    """Main function to run the GitHub agent."""
    parser = argparse.ArgumentParser(description="GitHub Agent")
    parser.add_argument("request", help="Request to send to the GitHub agent")
    args = parser.parse_args()
    
    try:
        agent = GitHubAgent()
        response = agent.process_request(args.request)
        print(response)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()