# Tekton Engineering Guidelines

This document outlines the engineering principles and practices for the Tekton ecosystem.

## Core Principles

- **Modularity**: All Tekton components should be modular and follow well-defined interfaces.
- **Interoperability**: Components should work together seamlessly while maintaining independence.
- **Performance Optimization**: Code should be optimized for the hardware it runs on.
- **User Experience**: APIs and interfaces should be intuitive and consistent.

## Data Storage Architecture

- **Centralized Database Services**:
  - All database services MUST be managed by Hermes as the central data management component
  - This includes all database types: vector stores, knowledge graphs, key-value stores, caches, etc.
  - No component should implement its own database connection or storage mechanism
  - Hardware-optimized implementations (e.g., Qdrant for Apple Silicon, FAISS for NVIDIA)
  - Automatic database selection based on hardware detection
  - Common data directory structure (`~/.tekton/`)
  - Environment variables for overriding default paths

- **Namespace Management**:
  - All data is organized into namespaces for client isolation
  - Cross-namespace indexing available for authorized operations
  - Comprehensive indexing across the full scope of data for analysis

- **Client Database Options**:
  - Agents, tools, and workflows can choose their database strategy:
    1. Generate isolated namespaces when data segregation is required
    2. Use existing namespaces when available and appropriate
    3. Use shared namespaces when integration is the priority

## Development Practices

- **Version Control**: Use Git for version control with meaningful commit messages.
- **Documentation**: All code should be well-documented with docstrings and READMEs.
- **Testing**: Write unit tests for all code with CI/CD integration.
- **Code Reviews**: All code changes should be reviewed by at least one other developer.

## Coding Standards

- **Python**: Follow PEP 8 style guide with type hints.
- **JavaScript/TypeScript**: Follow Airbnb JavaScript Style Guide.
- **Error Handling**: Use proper error handling with meaningful error messages.

## Logging Architecture

- **Centralized Logging System**:
  - All Tekton components MUST use the centralized logging system provided by Hermes
  - No component should implement its own logging mechanism or direct logs to stdout/files
  - Structured JSON format with standardized fields across all components
  - Schema versioning for all log entries to maintain backward compatibility

- **Log Entry Requirements**:
  - **Metadata Fields**:
    - `timestamp`: When the log entry was created (ISO 8601 format)
    - `effective_timestamp`: When the event actually occurred or should be considered effective
    - `component`: The specific Tekton component generating the log
    - `level`: Severity level (see Log Levels below)
    - `schema_version`: Version of the log schema being used
    - `correlation_id`: Unique identifier to track related operations across components
    - `client_id`: Identifier of the client or namespace associated with the log

  - **Log Levels**:
    - `FATAL`: At least one system component is inoperable causing a fatal error within the larger system, typically requiring immediate attention and system restart
    - `ERROR`: At least one system component is inoperable and is interfering with the operability of other functionalities
    - `WARN`: An unexpected event has occurred that may disrupt or delay other processes but does not prevent system operation
    - `INFO`: An event has occurred that does not appear to affect operations and usually can be ignored
    - `NORMAL`: System lifecycle events such as component startup/shutdown, user login/logout, or expected state transitions
    - `DEBUG`: Relevant details useful during software debugging or troubleshooting within test environments
    - `TRACE`: Execution of code with full visibility within the application or third-party libraries

  - **Content Fields**:
    - `message`: Human-readable description of the event
    - `code`: Machine-readable event code for categorization 
    - `context`: Additional structured data relevant to the event
    - `stack_trace`: For error logs, the full exception stack trace

- **Usage Patterns**:
  - Import the logging client from Hermes rather than using the standard Python logging
  - Include appropriate context data for all log entries
  - Set effective_timestamp explicitly when logging events that occurred at a different time
  - Use consistent event codes across components for similar operations

- **Retention and Analysis**:
  - Logs are stored in a database managed by Hermes for analysis and querying
  - Retention policies are defined based on log level and importance
  - Logs are indexed for efficient searching and pattern recognition
  - Analysis tools provided through Hermes API for log exploration

## Security Practices

- **Authentication**: Implement secure authentication for all user-facing interfaces.
- **Authorization**: Enforce proper access controls to protect sensitive data.
- **Data Security**: Encrypt sensitive data both in transit and at rest.
- **Dependency Management**: Regularly update dependencies to address security vulnerabilities.