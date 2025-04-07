from letta_client import Letta
import uuid
import os

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# Generate unique suffixes for tool names
unique_suffix = str(uuid.uuid4())[:8]

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
    "name": f"calculator_{unique_suffix}",
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
llm_config = {
    "model": "anthropic/claude-3-haiku-20240307",
    "temperature": 0.7,
    "max_tokens": 1000,
    "put_inner_thoughts_in_kwargs": True,
    "model_endpoint_type": "openai",  # Required field
    "context_window": 16000  # Required field
}

# Create embedding config with all required fields
embedding_config = {
    "model": "openai/text-embedding-ada-002",
    "embedding_endpoint_type": "openai",  # Required field
    "embedding_model": "text-embedding-ada-002",  # Required field
    "embedding_dim": 1536  # Required field for OpenAI embeddings
}

# Create the agent with required memory_blocks and LLM configuration
agent = client.agents.create(
    name=f"Calculator_Assistant_{unique_suffix}",
    description="An assistant that can perform mathematical calculations",
    system=system_prompt,
    memory_blocks=[],  # Required field
    tools=[calculator_tool.id],  # Use the created tool ID
    llm_config=llm_config,  # Add LLM configuration with all required fields
    embedding_config=embedding_config  # Add embedding configuration with all required fields
)

print(f"Created calculator agent with ID: {agent.id}")
print("Agent created successfully!")