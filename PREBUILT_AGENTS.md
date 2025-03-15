# Agenteer Pre-built Agents

This document describes the pre-built agents available in Agenteer along with their metadata. This information is used by Nexus to provide intelligent agent recommendations and descriptions.

## Agent Type Metadata

Each agent type has standard metadata that helps Nexus understand its capabilities:

```
{
    "type": "agent_type_name",
    "name": "Display Name",
    "description": "General description of the agent type",
    "capabilities": ["capability1", "capability2", ...],
    "keywords": ["keyword1", "keyword2", ...],
    "use_cases": ["use case 1", "use case 2", ...],
    "examples": ["example prompt 1", "example prompt 2", ...]
}
```

## Standard Agents

```json
{
    "type": "standard",
    "name": "Standard Agent",
    "description": "General-purpose agent for various tasks including coding, brainstorming, and answering questions",
    "capabilities": [
        "answer questions",
        "provide information",
        "assist with coding tasks",
        "brainstorm ideas",
        "explain concepts",
        "draft content"
    ],
    "keywords": [
        "standard", "basic", "default", "general", "assistant", 
        "code", "help", "question", "brainstorm", "explain"
    ],
    "use_cases": [
        "General question answering",
        "Code assistance",
        "Creative writing",
        "Research summaries",
        "Learning concepts"
    ],
    "examples": [
        "I need help with a Python script",
        "Explain quantum computing",
        "Brainstorm marketing ideas for my startup",
        "Help me debug this code",
        "Write a blog post about AI safety"
    ]
}
```

## Nexus Agents

```json
{
    "type": "nexus",
    "name": "Nexus Agent",
    "description": "Memory-enabled agent that maintains context across conversations",
    "capabilities": [
        "remember conversations", 
        "maintain context", 
        "recall previous interactions",
        "store important information",
        "provide personalized responses",
        "learn user preferences"
    ],
    "keywords": [
        "nexus", "memory", "remember", "context", "conversation", 
        "recall", "history", "personalized", "learn"
    ],
    "use_cases": [
        "Ongoing project assistance",
        "Learning about user preferences",
        "Personalized tutoring",
        "Contextual conversations",
        "Knowledge management"
    ],
    "examples": [
        "Remember that we were working on a Python project yesterday",
        "What did we discuss last time?",
        "Continue our conversation about marketing strategies",
        "Use what you know about me to suggest a book",
        "Let's continue where we left off"
    ]
}
```

## GitHub Agents

```json
{
    "type": "github",
    "name": "GitHub Agent",
    "description": "Specialized agent for GitHub repository management and code-related tasks",
    "capabilities": [
        "list repositories",
        "get repository details",
        "create repositories",
        "manage pull requests",
        "view issues",
        "create/edit/delete files",
        "analyze repository content"
    ],
    "keywords": [
        "github", "git", "repo", "repository", "code", "pull", 
        "commit", "issue", "branch", "PR", "pull request"
    ],
    "use_cases": [
        "GitHub repository management",
        "Code review assistance",
        "Issue tracking",
        "Repository analysis",
        "Repository creation and setup"
    ],
    "examples": [
        "List my GitHub repositories",
        "Create a new repository called MyProject",
        "Show me the open issues in repository X",
        "Create a pull request for my changes",
        "Help me set up a GitHub workflow"
    ]
}
```

## Mail Agents

```json
{
    "type": "mail",
    "name": "Mail Agent",
    "description": "Email management agent that can read, send, and organize emails",
    "capabilities": [
        "send emails",
        "read emails",
        "search inbox",
        "manage drafts",
        "handle attachments",
        "organize emails",
        "respond to messages"
    ],
    "keywords": [
        "mail", "email", "gmail", "outlook", "message", "send", "inbox", 
        "imap", "smtp", "reply", "compose", "draft"
    ],
    "use_cases": [
        "Email management",
        "Inbox organization",
        "Email composition assistance",
        "Email response drafting",
        "Email searching and filtering"
    ],
    "examples": [
        "Check my latest emails",
        "Send an email to john@example.com",
        "Find emails about the quarterly report",
        "Draft a response to the last email from Sarah",
        "Summarize my unread messages"
    ]
}
```

## Browser Agents

```json
{
    "type": "browser",
    "name": "Browser Agent",
    "description": "Web browsing agent that can navigate and interact with websites",
    "capabilities": [
        "navigate websites",
        "extract content",
        "fill forms",
        "click buttons",
        "take screenshots",
        "search the web",
        "analyze web pages"
    ],
    "keywords": [
        "browser", "web", "chrome", "firefox", "internet", "website", 
        "browse", "surf", "navigate", "webpage", "search"
    ],
    "use_cases": [
        "Web research",
        "Data extraction from websites",
        "Web form automation",
        "Web content summarization",
        "Website testing and analysis"
    ],
    "examples": [
        "Visit https://example.com and summarize the content",
        "Search for information about climate change",
        "Fill out the contact form on my website",
        "Find the latest news about artificial intelligence",
        "Take a screenshot of the homepage"
    ]
}
```

## Creating Pre-built Agents

To streamline the onboarding experience, Agenteer can automatically create pre-built agents of each type. The following will create a set of agents with proper configuration:

```bash
# Create a standard agent
agenteer create -n "GeneralAssistant" -d "General-purpose assistant for various tasks" -t standard

# Create a memory-enabled Nexus agent
agenteer create -n "MemoryAssistant" -d "Memory-enabled assistant that remembers context" -t nexus

# Create a GitHub agent
agenteer create -n "GitHubAssistant" -d "GitHub repository management and code assistant" -t github

# Create a Mail agent
agenteer create -n "MailAssistant" -d "Email management assistant for Gmail and Outlook" -t mail

# Create a Browser agent
agenteer create -n "WebBrowser" -d "Web browsing assistant for research and interaction" -t browser
```

This set of agents provides a comprehensive starting point for new users, covering the most common use cases.