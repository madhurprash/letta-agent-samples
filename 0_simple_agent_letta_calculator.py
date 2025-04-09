from letta_client import Letta
import uuid
import os

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# List available models and print them out
available_models = client.models.list_llms()
print("\nAvailable models:")
for i, model in enumerate(available_models):
    print(f"{i+1}. {model.handle} ({model.model_endpoint_type})")
print("\n")

# Generate unique suffixes for tool names
unique_suffix = str(uuid.uuid4())[:8]

anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", None)

# Print the API key status (without revealing the full key for security)
if anthropic_api_key:
    masked_key = anthropic_api_key[:8] + "..." + anthropic_api_key[-4:]
    print(f"Found Anthropic API key: {masked_key}")
else:
    print("No Anthropic API key found in environment variables")

# System prompt for the calculator agent
system_prompt = """You are a helpful calculator assistant designed to perform mathematical operations.

You can perform basic arithmetic operations using the calculator tool:
- Addition
- Subtraction
- Multiplication
- Division

When a user asks you to perform a calculation, use the calculator tool with the appropriate operation.
Always verify inputs before calculating and check if division operations might involve division by zero.

Be helpful and friendly in your responses. If the user asks for a calculation you cannot perform,
explain what operations you can handle.
"""

# Create the calculator tool with source code
calculator_source_code = """
def calculator(operation: str, a: float, b: float) -> str:
    \"\"\"
    Perform a basic mathematical operation.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
        
    Returns:
        The result of the calculation as a string
    \"\"\"
    if operation.lower() == "add":
        return f"The result of {a} + {b} is {a + b}"
    elif operation.lower() == "subtract":
        return f"The result of {a} - {b} is {a - b}"
    elif operation.lower() == "multiply":
        return f"The result of {a} * {b} is {a * b}"
    elif operation.lower() == "divide":
        if b == 0:
            return "Error: Cannot divide by zero"
        return f"The result of {a} / {b} is {a / b}"
    else:
        return f"Unknown operation: {operation}"
"""

# Add a descriptor to the json_schema to include a name for the tool
tool_schema = {
    "name": f"new_tool_{unique_suffix}",
    "description": "A tool that performs basic arithmetic operations",
    "type": "function"
}

# Create the calculator tool
calculator_tool = client.tools.create(
    source_code=calculator_source_code,
    description=f"Calculator Tool {unique_suffix}",
    source_type="python",
    tags=["math", "calculator"],
    json_schema=tool_schema
)

print(f"Created calculator tool with ID: {calculator_tool.id}")

# Create LLM config with all required fields
# Using Claude 3.7 Sonnet as it's the latest model available
llm_config = {
    "model": "anthropic/claude-3.5-sonnet",  # Using the latest Claude model
    "temperature": 0.7,
    "max_tokens": 1000,
    "put_inner_thoughts_in_kwargs": False,  # Match the server's configuration
    "model_endpoint_type": "anthropic",
    "context_window": 200000  # Match the server's configuration
}

bedrock_llm_config = {
    "model": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",  # Using the latest Claude model
    "temperature": 0.7,
    "max_tokens": 1000,
    "put_inner_thoughts_in_kwargs": False,  # Match the server's configuration
    "model_endpoint_type": "bedrock",
    "context_window": 200000  # Match the server's configuration
}

# Create embedding config with all required fields
embedding_config = {
    "model": "openai/text-embedding-ada-002",
    "embedding_endpoint_type": "openai",
    "embedding_model": "text-embedding-ada-002",
    "embedding_dim": 1536
}

# Create the agent with required memory_blocks and LLM configuration
agent = client.agents.create(
    name=f"calculator_Assistant_{unique_suffix}",
    description="An assistant that can perform mathematical calculations",
    system=system_prompt,
    memory_blocks=[],
    tools=[calculator_tool.id],
    llm_config=bedrock_llm_config,
    embedding_config=embedding_config
)

print(f"Created calculator agent with ID: {agent.id}")
print("Agent created successfully!")