# Model Context Protocol (MCP) Overview

## Key Concepts
MCP is an open, schema-driven protocol that standardizes how language models connect to external tools, data, and functions via secure client-server communication over JSON-RPC 2.0. The protocol separates tool discovery, schema validation, and execution, with capabilities described using JSON Schema (Draft 2020-12) for input/output structure validation.

## Architectural Components
- **Host**: The application or platform that hosts the LLM and manages user interactions. It acts as the entry point for user requests and routes them to appropriate clients.
- **Client**: The component that connects to the server and manages the interaction between the LLM and external tools. It handles tool discovery, schema validation, and execution.
- **Server**: The external tool or service that provides specific capabilities (e.g., data access, function execution). Servers offer focused, composable features and operate within isolated environments.

## Communication Flow
1. User interacts with the Host application.
2. The Host directs the Client to connect to one or more Servers.
3. The Client discovers available capabilities through tool discovery.
4. The Client validates tool inputs using JSON Schema before execution.
5. The Client invokes the appropriate tool on the Server.
6. The Server executes the requested function and returns results.
7. The Client returns the results to the Host, which presents them to the user.

## Key Principles
- **Standardization**: Provides a universal protocol for AI connectivity, enabling interoperability across different implementations.
- **Simplicity**: Maintains a straightforward core protocol while supporting advanced features.
- **Extensibility**: Supports evolution through versioning and capability negotiation, allowing new features to be added without breaking existing systems.
- **Security**: Enforces strict isolation (servers cannot access full conversation history or cross-server data) and requires explicit user consent for sensitive operations.
- **Composability**: Enables dynamic composition of capabilities across different servers, supporting multi-agent workflows and complex interactions.