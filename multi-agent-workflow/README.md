# Multi-Agent Systems

All AI agents in `Letta` are stateful. Whenever you build a multi agent system in `Letta`, each of the agent can run both independently and with others via cross agent messaging. `Letta` provides tools for cross messaging between agents. To enable multi-agent collaboration with `Letta`, you can do so by accessing the built-in cross-agent communication tools. This can be done on the agent developer environment or through the SDK. View some of the built in cross agent communication tools below:

There are three built-in tools for cross-agent communication:

1. `send_message_to_agent_async` for asynchronous multi-agent messaging,

1. `send_message_to_agent_and_wait_for_reply` for synchronous multi-agent messaging, and 

1. `send_message_to_agents_matching_all_tags` for a “supervisor-worker” pattern

So the two main value propositions of using Multi agents with `Letta` are:

1. You can enable `synchronous` and `asynchronous` communication between agents through the tools that `Letta` offers. This can be for agent to agent or supervisor to a set of agents in a workflow.

- **Use custom agent to agent communication**: `Letta` enables users to write custom agent communication tools by using the `Letta` API. Since `Letta` runs as a service, you can make the request to the server from a custom tool to send messages to other agents via API calls.

2. `Letta` agents also share the state via shared memory blocks. This allows the agent to have a shared memory. You can share blocks between agents by attaching the same `block id` to multiple agents. 