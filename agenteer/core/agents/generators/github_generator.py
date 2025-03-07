"""
GitHub agent generator for Agenteer.

This module provides specialized functions for generating GitHub agents.
"""

import json
from typing import Dict, Any, List, Optional

from agenteer.core.llm.client import LLMClient


def get_github_tools() -> List[Dict[str, Any]]:
    """
    Get the list of GitHub tools that can be used by the agent.
    
    Returns:
        List of tool definitions for GitHub operations
    """
    return [
        {
            "name": "list_repositories",
            "description": "List repositories for the authenticated user",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "visibility": {
                        "type": "string",
                        "enum": ["all", "public", "private"],
                        "description": "Filter repositories by visibility"
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["created", "updated", "pushed", "full_name"],
                        "description": "Sort repositories by field"
                    }
                },
                "required": []
            })
        },
        {
            "name": "create_repository",
            "description": "Create a new GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the repository"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the repository"
                    },
                    "private": {
                        "type": "boolean",
                        "description": "Whether the repository is private"
                    },
                    "auto_init": {
                        "type": "boolean",
                        "description": "Initialize repository with README"
                    },
                    "gitignore_template": {
                        "type": "string",
                        "description": "Optional gitignore template name"
                    },
                    "license_template": {
                        "type": "string",
                        "description": "Optional license template name"
                    }
                },
                "required": ["name"]
            })
        },
        {
            "name": "delete_repository",
            "description": "Delete a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    }
                },
                "required": ["repo_name"]
            })
        },
        {
            "name": "get_repository",
            "description": "Get details of a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    }
                },
                "required": ["repo_name"]
            })
        },
        {
            "name": "create_issue",
            "description": "Create a new issue in a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the issue"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body of the issue"
                    },
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of label names to add to the issue"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of usernames to assign to the issue"
                    }
                },
                "required": ["repo_name", "title"]
            })
        },
        {
            "name": "list_issues",
            "description": "List issues from a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    },
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "Filter issues by state"
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["created", "updated", "comments"],
                        "description": "Sort issues by field"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort direction"
                    },
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Filter issues by labels"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return"
                    }
                },
                "required": ["repo_name"]
            })
        },
        {
            "name": "create_pull_request",
            "description": "Create a pull request in a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the pull request"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body of the pull request"
                    },
                    "head": {
                        "type": "string",
                        "description": "Head branch name (source branch)"
                    },
                    "base": {
                        "type": "string",
                        "description": "Base branch name (target branch)"
                    }
                },
                "required": ["repo_name", "title", "head", "base"]
            })
        },
        {
            "name": "list_branches",
            "description": "List branches in a GitHub repository",
            "function_def": json.dumps({
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Full name of the repository (username/repo) or just repo name"
                    }
                },
                "required": ["repo_name"]
            })
        }
    ]


async def generate_github_tools_file(
    llm_client: LLMClient,
    name: str
) -> str:
    """
    Generate the GitHub tools file implementation for an agent.
    
    This function creates a specialized tools file with GitHub functionality
    that can be used by the agent to interact with GitHub.
    
    Args:
        llm_client: LLM client instance
        name: Name of the agent
        
    Returns:
        Generated GitHub tools file content
    """
    # For GitHub tools, we'll provide a specific implementation rather than
    # generating with LLM, to ensure proper functionality
    
    tools_file = f"""
# GitHub tools for {name} agent
from typing import Dict, Any, List, Optional, Union
import json
import os
from github import Github, GithubException, BadCredentialsException, UnknownObjectException
from agenteer.utils.config.settings import settings
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Initialize GitHub client
def init_github_client():
    \"\"\"Initialize GitHub client with token from settings.\"\"\"
    token = settings.github_api_token
    if not token:
        raise ValueError("GitHub API token not found in settings")
    return Github(token)

def list_repositories(visibility: Optional[str] = "all", sort: Optional[str] = "updated") -> str:
    \"\"\"
    List repositories for the authenticated user.
    
    Args:
        visibility: Filter repositories by visibility (all, public, private)
        sort: Sort repositories by field (created, updated, pushed, full_name)
        
    Returns:
        JSON string with list of repositories
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Get repositories
        repos = user.get_repos(visibility=visibility, sort=sort)
        
        # Convert to list
        repo_list = []
        for repo in repos:
            repo_list.append({{
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "private": repo.private,
                "fork": repo.fork,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "language": repo.language,
                "default_branch": repo.default_branch
            }})
        
        return json.dumps(repo_list, indent=2)
    
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except Exception as e:
        logger.error(f"Error listing repositories: {{str(e)}}")
        return json.dumps({{"error": f"Error listing repositories: {{str(e)}}"}})

def create_repository(
    name: str,
    description: Optional[str] = None,
    private: Optional[bool] = False,
    auto_init: Optional[bool] = True,
    gitignore_template: Optional[str] = None,
    license_template: Optional[str] = None
) -> str:
    \"\"\"
    Create a new GitHub repository.
    
    Args:
        name: Name of the repository
        description: Optional description of the repository
        private: Whether the repository is private
        auto_init: Initialize repository with README
        gitignore_template: Optional gitignore template name
        license_template: Optional license template name
        
    Returns:
        JSON string with repository details or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Create repository
        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=auto_init,
            gitignore_template=gitignore_template,
            license_template=license_template
        )
        
        # Return repo details
        return json.dumps({{
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "private": repo.private,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "default_branch": repo.default_branch
        }}, indent=2)
    
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except GithubException as e:
        logger.error(f"GitHub error creating repository: {{str(e)}}")
        return json.dumps({{
            "error": f"GitHub error creating repository: {{e.data.get('message', str(e))}}",
            "status_code": e.status
        }})
    except Exception as e:
        logger.error(f"Error creating repository: {{str(e)}}")
        return json.dumps({{"error": f"Error creating repository: {{str(e)}}"}})

def delete_repository(repo_name: str) -> str:
    \"\"\"
    Delete a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        
    Returns:
        JSON string with success or error message
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' in repo_name:
            username, repo = repo_name.split('/')
            if username != user.login:
                return json.dumps({{"error": f"You can only delete your own repositories. Got {{username}} but authenticated as {{user.login}}"}})
            repo_name = repo
        
        # Get repository
        repo = user.get_repo(repo_name)
        
        # Delete repository
        repo.delete()
        
        return json.dumps({{"success": True, "message": f"Repository {{repo_name}} deleted successfully"}})
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except GithubException as e:
        logger.error(f"GitHub error deleting repository: {{str(e)}}")
        return json.dumps({{
            "error": f"GitHub error deleting repository: {{e.data.get('message', str(e))}}",
            "status_code": e.status
        }})
    except Exception as e:
        logger.error(f"Error deleting repository: {{str(e)}}")
        return json.dumps({{"error": f"Error deleting repository: {{str(e)}}"}})

def get_repository(repo_name: str) -> str:
    \"\"\"
    Get details of a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        
    Returns:
        JSON string with repository details or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' not in repo_name:
            repo_name = f"{{user.login}}/{{repo_name}}"
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Return repo details
        return json.dumps({{
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
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url
        }}, indent=2)
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except Exception as e:
        logger.error(f"Error getting repository: {{str(e)}}")
        return json.dumps({{"error": f"Error getting repository: {{str(e)}}"}})

def create_issue(
    repo_name: str,
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None
) -> str:
    \"\"\"
    Create a new issue in a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        title: Title of the issue
        body: Body of the issue
        labels: List of label names to add to the issue
        assignees: List of usernames to assign to the issue
        
    Returns:
        JSON string with issue details or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' not in repo_name:
            repo_name = f"{{user.login}}/{{repo_name}}"
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Create issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees
        )
        
        # Return issue details
        return json.dumps({{
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "url": issue.html_url,
            "state": issue.state,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees]
        }}, indent=2)
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except GithubException as e:
        logger.error(f"GitHub error creating issue: {{str(e)}}")
        return json.dumps({{
            "error": f"GitHub error creating issue: {{e.data.get('message', str(e))}}",
            "status_code": e.status
        }})
    except Exception as e:
        logger.error(f"Error creating issue: {{str(e)}}")
        return json.dumps({{"error": f"Error creating issue: {{str(e)}}"}})

def list_issues(
    repo_name: str,
    state: Optional[str] = "open",
    sort: Optional[str] = "created",
    direction: Optional[str] = "desc",
    labels: Optional[List[str]] = None,
    limit: Optional[int] = 10
) -> str:
    \"\"\"
    List issues from a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        state: Filter issues by state (open, closed, all)
        sort: Sort issues by field (created, updated, comments)
        direction: Sort direction (asc, desc)
        labels: Filter issues by labels
        limit: Maximum number of issues to return
        
    Returns:
        JSON string with list of issues or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' not in repo_name:
            repo_name = f"{{user.login}}/{{repo_name}}"
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Get issues
        issues = repo.get_issues(state=state, sort=sort, direction=direction, labels=labels)
        
        # Convert to list
        issue_list = []
        for i, issue in enumerate(issues):
            if i >= limit:
                break
            
            issue_list.append({{
                "number": issue.number,
                "title": issue.title,
                "body": issue.body[:100] + "..." if issue.body and len(issue.body) > 100 else issue.body,
                "url": issue.html_url,
                "state": issue.state,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees]
            }})
        
        return json.dumps(issue_list, indent=2)
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except Exception as e:
        logger.error(f"Error listing issues: {{str(e)}}")
        return json.dumps({{"error": f"Error listing issues: {{str(e)}}"}})

def create_pull_request(
    repo_name: str,
    title: str,
    body: str,
    head: str,
    base: str
) -> str:
    \"\"\"
    Create a pull request in a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        title: Title of the pull request
        body: Body of the pull request
        head: Head branch name (source branch)
        base: Base branch name (target branch)
        
    Returns:
        JSON string with pull request details or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' not in repo_name:
            repo_name = f"{{user.login}}/{{repo_name}}"
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Create pull request
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )
        
        # Return pull request details
        return json.dumps({{
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "url": pr.html_url,
            "state": pr.state,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            "merged": pr.merged,
            "mergeable": pr.mergeable,
            "mergeable_state": pr.mergeable_state,
            "head": pr.head.ref,
            "base": pr.base.ref
        }}, indent=2)
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except GithubException as e:
        logger.error(f"GitHub error creating pull request: {{str(e)}}")
        return json.dumps({{
            "error": f"GitHub error creating pull request: {{e.data.get('message', str(e))}}",
            "status_code": e.status
        }})
    except Exception as e:
        logger.error(f"Error creating pull request: {{str(e)}}")
        return json.dumps({{"error": f"Error creating pull request: {{str(e)}}"}})

def list_branches(
    repo_name: str,
) -> str:
    \"\"\"
    List branches in a GitHub repository.
    
    Args:
        repo_name: Full name of the repository (username/repo) or just repo name
        
    Returns:
        JSON string with list of branches or error
    \"\"\"
    try:
        g = init_github_client()
        user = g.get_user()
        
        # Check if repo_name includes username
        if '/' not in repo_name:
            repo_name = f"{{user.login}}/{{repo_name}}"
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Get branches
        branches = repo.get_branches()
        
        # Convert to list
        branch_list = []
        for branch in branches:
            branch_list.append({{
                "name": branch.name,
                "protected": branch.protected,
                "is_default": branch.name == repo.default_branch
            }})
        
        return json.dumps(branch_list, indent=2)
    
    except UnknownObjectException:
        return json.dumps({{"error": f"Repository {{repo_name}} not found"}})
    except BadCredentialsException:
        return json.dumps({{"error": "Invalid GitHub credentials"}})
    except Exception as e:
        logger.error(f"Error listing branches: {{str(e)}}")
        return json.dumps({{"error": f"Error listing branches: {{str(e)}}"}})
"""
    
    return tools_file


async def generate_github_agent_file(
    llm_client: LLMClient,
    name: str
) -> str:
    """
    Generate the GitHub agent file implementation.
    
    Args:
        llm_client: LLM client instance
        name: Name of the agent
        
    Returns:
        Generated GitHub agent file content
    """
    # For the main agent file, we'll also provide a specialized implementation
    
    agent_file = f"""
# GitHub agent for {name}
from typing import Dict, Any, List, Optional, Union
import json
import os
import logging

# Import agent tools
from agent_tools import (
    list_repositories, 
    create_repository, 
    delete_repository, 
    get_repository,
    create_issue,
    list_issues,
    create_pull_request,
    list_branches
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class GitHubAgent:
    \"\"\"
    GitHub Agent that can create, delete and manage repositories,
    as well as issues, pull requests, and other GitHub operations.
    \"\"\"
    
    def __init__(self):
        \"\"\"Initialize the GitHub agent.\"\"\"
        logger.info("Initializing GitHub agent")
    
    def process_request(self, request: str) -> str:
        \"\"\"
        Process a request and route it to the appropriate GitHub function.
        
        This is a simple request parser that tries to identify the user's intent
        and call the correct GitHub function. In a real agent, this would use
        an LLM to parse intents and arguments more intelligently.
        
        Args:
            request: The user's request string
            
        Returns:
            Response from the GitHub API or error message
        \"\"\"
        request = request.lower().strip()
        
        # List repositories
        if "list repositories" in request or "show repos" in request or "show repositories" in request:
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
                
            return list_repositories(visibility=visibility, sort=sort)
        
        # Create repository
        elif "create repository" in request or "create repo" in request:
            # Extract repository name (simple heuristic)
            name_parts = request.split("named ")
            if len(name_parts) > 1:
                name_candidate = name_parts[1].split()[0].strip()
                
                # Remove punctuation
                name = name_candidate.strip('.,;:"\'()[]{{}}')
                
                # Extract description (simple heuristic)
                description = None
                desc_parts = request.split("description ")
                if len(desc_parts) > 1:
                    description = desc_parts[1].split(".")[0].strip()
                
                # Check if private
                private = "private" in request
                
                return create_repository(
                    name=name,
                    description=description,
                    private=private,
                    auto_init=True
                )
            else:
                return json.dumps({{"error": "Could not determine repository name from request"}})
        
        # Delete repository
        elif "delete repository" in request or "delete repo" in request:
            # Extract repository name (simple heuristic)
            name_parts = request.split("named ")
            if len(name_parts) > 1:
                name_candidate = name_parts[1].split()[0].strip()
                
                # Remove punctuation
                name = name_candidate.strip('.,;:"\'()[]{{}}')
                
                return delete_repository(repo_name=name)
            else:
                return json.dumps({{"error": "Could not determine repository name from request"}})
        
        # Get repository
        elif "get repository" in request or "get repo" in request or "show repository" in request:
            # Extract repository name (simple heuristic)
            name_parts = request.split("named ")
            if len(name_parts) > 1:
                name_candidate = name_parts[1].split()[0].strip()
                
                # Remove punctuation
                name = name_candidate.strip('.,;:"\'()[]{{}}')
                
                return get_repository(repo_name=name)
            else:
                return json.dumps({{"error": "Could not determine repository name from request"}})
        
        # Create issue
        elif "create issue" in request:
            # Extract repository name (simple heuristic)
            repo_name = None
            name_parts = request.split("in repo ")
            if len(name_parts) > 1:
                repo_name = name_parts[1].split()[0].strip()
                repo_name = repo_name.strip('.,;:"\'()[]{{}}')
            
            # Extract issue title (simple heuristic)
            title = None
            title_parts = request.split("titled ")
            if len(title_parts) > 1:
                title = title_parts[1].split(".")[0].strip()
                title = title.strip('.,;:"\'')
            
            # Extract issue body (simple heuristic)
            body = None
            body_parts = request.split("with body ")
            if len(body_parts) > 1:
                body = body_parts[1].strip()
            
            if repo_name and title:
                return create_issue(
                    repo_name=repo_name,
                    title=title,
                    body=body
                )
            else:
                return json.dumps({{"error": "Could not determine repository name or issue title from request"}})
        
        # List issues
        elif "list issues" in request:
            # Extract repository name (simple heuristic)
            repo_name = None
            name_parts = request.split("in repo ")
            if len(name_parts) > 1:
                repo_name = name_parts[1].split()[0].strip()
                repo_name = repo_name.strip('.,;:"\'()[]{{}}')
            
            if repo_name:
                # Determine state
                state = "open"
                if "closed" in request:
                    state = "closed"
                elif "all" in request:
                    state = "all"
                
                return list_issues(
                    repo_name=repo_name,
                    state=state
                )
            else:
                return json.dumps({{"error": "Could not determine repository name from request"}})
        
        # Create pull request
        elif "create pull request" in request or "create pr" in request:
            # Extract repository name (simple heuristic)
            repo_name = None
            name_parts = request.split("in repo ")
            if len(name_parts) > 1:
                repo_name = name_parts[1].split()[0].strip()
                repo_name = repo_name.strip('.,;:"\'()[]{{}}')
            
            # Extract PR title (simple heuristic)
            title = None
            title_parts = request.split("titled ")
            if len(title_parts) > 1:
                title = title_parts[1].split(".")[0].strip()
                title = title.strip('.,;:"\'')
            
            # Extract head and base branches (simple heuristic)
            head = None
            base = "main"  # Default to main
            
            from_parts = request.split("from branch ")
            if len(from_parts) > 1:
                head = from_parts[1].split()[0].strip()
                head = head.strip('.,;:"\'()[]{{}}')
            
            to_parts = request.split("to branch ")
            if len(to_parts) > 1:
                base = to_parts[1].split()[0].strip()
                base = base.strip('.,;:"\'()[]{{}}')
            
            if repo_name and title and head:
                body = f"Pull request from {{head}} to {{base}}"
                
                # Extract PR body if provided
                body_parts = request.split("with body ")
                if len(body_parts) > 1:
                    body = body_parts[1].strip()
                
                return create_pull_request(
                    repo_name=repo_name,
                    title=title,
                    body=body,
                    head=head,
                    base=base
                )
            else:
                return json.dumps({{"error": "Could not determine repository name, title, or branches from request"}})
        
        # List branches
        elif "list branches" in request:
            # Extract repository name (simple heuristic)
            repo_name = None
            name_parts = request.split("in repo ")
            if len(name_parts) > 1:
                repo_name = name_parts[1].split()[0].strip()
                repo_name = repo_name.strip('.,;:"\'()[]{{}}')
            
            if repo_name:
                return list_branches(repo_name=repo_name)
            else:
                return json.dumps({{"error": "Could not determine repository name from request"}})
        
        # Unknown request
        else:
            return json.dumps({{
                "error": "Unknown GitHub request. Try one of these: list repositories, create repository, delete repository, get repository, create issue, list issues, create pull request, list branches"
            }})

# Create an instance of the agent
github_agent = GitHubAgent()

def process_request(request: str) -> str:
    \"\"\"Process a request through the GitHub agent.\"\"\"
    return github_agent.process_request(request)

# Sample usage
if __name__ == "__main__":
    # Test the agent
    test_request = "list repositories"
    response = process_request(test_request)
    print(f"Request: {{test_request}}")
    print(f"Response: {{response}}")
"""
    
    return agent_file