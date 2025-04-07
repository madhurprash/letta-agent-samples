from letta_client import Letta
import uuid
import os

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# Generate unique suffixes for tool names
unique_suffix = str(uuid.uuid4())[:8]

# Define calculator function
def calculator(operation: str, a: float, b: float) -> str:
    """
    Perform a basic mathematical operation.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
        
    Returns:
        The result of the calculation as a string
    """
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

# Create the calculator tool
calculator_tool = client.tools.upsert_from_function(
    func=calculator,
)

# Create the calculator agent
agent = client.agents.create(
    name=f"Calculator_Assistant_{unique_suffix}",
    description="An assistant that can perform mathematical calculations",
    system=system_prompt,
    memory_blocks=[],
    tool_ids=[calculator_tool.id],
    tools=["send_message"],  # allows for generation of `AssistantMessage`
    include_base_tools=True,
    model="anthropic/claude-3-haiku-20240307",  # You can change to another model if needed
    embedding="openai/text-embedding-ada-002",
    tool_rules=[
        {
            "type": "constrain_child_tools",
            "tool_name": "calculator",
            "children": ["send_message"]
        },
        {
            "type": "exit_loop",
            "tool_name": "send_message"
        }
    ],
)

print(f"Created calculator agent with ID: {agent.id}")
print("Tools:", [t.name for t in agent.tools])