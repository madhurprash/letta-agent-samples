# Import the necessary libraries
import os
import uuid
from letta_client import Letta

# Connect to the Letta server first
client = Letta(base_url="http://localhost:8283")

anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", None)

# Print the API key status (without revealing the full key for security)
if anthropic_api_key:
    masked_key = anthropic_api_key[:8] + "..." + anthropic_api_key[-4:]
    print(f"Found Anthropic API key: {masked_key}")
else:
    print("No Anthropic API key found in environment variables")

# Next, create a unique id that will be appended to the agent names - this can
# be for the supervisor agent or the worker agent in this case
unique_id = str(uuid.uuid4())[:8]

# Next, we will create a shared block that will be used between the agents. In this case
# will add some dummy information to the shared block
# Create a simpler shared memory block for task coordination

# These are a list of active task with basic details, there is a shared team note, a time stamp for
# when the block was updated as well.
shared_block = client.blocks.create(
    label="team_tasks",
    value="""
{
  "active_tasks": [
    {
      "id": "task-001",
      "description": "Analyze quarterly sales data",
      "assigned_to": "worker_1",
      "status": "in_progress",
      "due_date": "2025-04-15"
    },
    {
      "id": "task-002",
      "description": "Create summary report",
      "assigned_to": "worker_2",
      "status": "pending",
      "due_date": "2025-04-20"
    },
    {
      "id": "task-003",
      "description": "Prepare presentation slides",
      "assigned_to": "worker_3",
      "status": "not_started",
      "due_date": "2025-04-25"
    }
  ],
  "team_notes": "Focus on highlighting Q1 growth trends in the eastern region",
  "last_updated": "2025-04-09T08:00:00Z"
}
"""
)

print(f"Created shared memory block with ID: {shared_block.id}")

# Represents the system prompt for the supervisor agent
supervisor_prompt: str = """
You are a supervisor agent responsible for coordinating a team of worker agents.
Your responsibilities include:
1. Assigning tasks to worker agents
2. Monitoring progress
3. Consolidating results from workers
4. Making decisions based on worker agent outputs

Use the send_message_to_agents_matching_all_tags tool to broadcast instructions to all workers.
Use the shared memory block to track overall team progress.
"""

# Prompt for worker agents
worker_prompt: str = """
You are a worker agent that performs tasks assigned by a supervisor.
Your responsibilities include:
1. Receiving tasks from the supervisor
2. Completing assigned tasks to the best of your ability
3. Reporting results back to the supervisor
4. Updating the shared memory with your progress

Use the send_message_to_agent_and_wait_for_reply tool to communicate with the supervisor.
Use the shared memory block to log your progress and see what other workers are doing.
"""

# create the supervisor agent
supervisor_agent = client.agents.create(
    name=f"supervisor_{unique_id}",
    description="Task coordinator for worker agents",
    system=supervisor_prompt,
    memory_blocks=[{"label": "persona", "value": "I am the supervisor agent. I coordinate tasks among worker agents."}],
    # attach the shared block from above, give it access to a build in tool to send
    # the task across all worker agents
    block_ids=[shared_block.id],
    tools=["send_message_to_agents_matching_all_tags"],
    # llm config
    model='anthropic/claude-3-5-sonnet-20241022',
    embedding_config={
        "model": "openai/text-embedding-ada-002",
        "embedding_endpoint_type": "openai",
        "embedding_model": "text-embedding-ada-002",
        "embedding_dim": 1536
    },
    tags=["supervisor_agent"]
)

print(f"Created supervisor agent with ID: {supervisor_agent.id}")

# Create multiple worker agents
worker_agents = []
# In this case, we will create 3 worker agents
for i in range(3):
    worker_agent = client.agents.create(
        name=f"worker_{i}_{unique_id}",
        description=f"Worker agent {i} that completes tasks",
        system=worker_prompt,
        memory_blocks=[{"label": "persona", "value": f"I am worker agent {i}. I complete tasks assigned by the supervisor."}],
        block_ids=[shared_block.id],  # Attach the shared memory block
        # Synchronous agent communication. This will be used until the agent has 
        # a response and can provide that back to the supervisor agent
        tools=["send_message_to_agent_and_wait_for_reply"],
        model='anthropic/claude-3-haiku-20240307',
        embedding_config={
            "model": "openai/text-embedding-ada-002",
            "embedding_endpoint_type": "openai",
            "embedding_model": "text-embedding-ada-002",
            "embedding_dim": 1536
        },
        tags=["worker_agent"]
    )
    worker_agents.append(worker_agent)
    print(f"Created worker agent {i} with ID: {worker_agent.id}")

# Start the workflow by sending a message to the supervisor
worker_ids = [agent.id for agent in worker_agents]
initial_message = f"Hi! How are you?"
response = client.agents.messages.create(
    agent_id=supervisor_agent.id,
    messages=[
        {
            "role": "user",
            "content": initial_message
        }
    ]
)

print(f"Initial message sent to supervisor: {response}")
print("Multi-agent system is now running!")

# After sending the initial message
for i, worker in enumerate(worker_agents):
    worker_messages = client.agents.messages.list(agent_id=worker.id)
    print(f"Worker {i} messages: {worker_messages}")
    
# Check if supervisor received any responses
supervisor_messages = client.agents.messages.list(agent_id=supervisor_agent.id)
print(f"Supervisor messages after initial assignment: {supervisor_messages}")