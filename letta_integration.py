from letta_client import Letta
import uuid

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# Generate unique suffixes for tool names
unique_suffix = str(uuid.uuid4())[:8]

# Define calculator functions
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

def langgraph_calculator(operation: str, a: float, b: float) -> str:
    """
    Perform a calculation using LangGraph workflow.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
        
    Returns:
        The result of the calculation
    """
    from langgraph.graph import StateGraph, END
    from typing import TypedDict, Optional
    
    # Define a simple state for our calculator
    class CalcState(TypedDict):
        operation: str
        a: float
        b: float
        result: Optional[float]
        error: Optional[str]
    
    # Function to perform the calculation
    def calculate(state: CalcState) -> CalcState:
        op = state["operation"].lower()
        a = state["a"]
        b = state["b"]
        
        try:
            if op == "add":
                return {**state, "result": a + b}
            elif op == "subtract":
                return {**state, "result": a - b}
            elif op == "multiply":
                return {**state, "result": a * b}
            elif op == "divide":
                if b == 0:
                    return {**state, "error": "Cannot divide by zero"}
                return {**state, "result": a / b}
            else:
                return {**state, "error": f"Unknown operation: {op}"}
        except Exception as e:
            return {**state, "error": str(e)}
    
    # Function to format the result
    def format_result(state: CalcState) -> CalcState:
        if "error" in state and state["error"]:
            return {**state, "formatted_result": f"Error: {state['error']}"}
        
        result = state["result"]
        # Format to remove trailing zeros
        if result == int(result):
            formatted = str(int(result))
        else:
            formatted = str(result).rstrip('0').rstrip('.')
            
        return {**state, "formatted_result": f"The result of {a} {operation} {b} is {formatted}"}
    
    # Create the graph
    workflow = StateGraph(CalcState)
    workflow.add_node("calculate", calculate)
    workflow.add_node("format", format_result)
    workflow.set_entry_point("calculate")
    workflow.add_edge("calculate", "format")
    workflow.add_edge("format", END)
    
    # Run the workflow
    app = workflow.compile()
    result = app.invoke({
        "operation": operation,
        "a": a,
        "b": b
    })
    
    # Return the formatted result or error
    if "error" in result and result["error"]:
        return f"Error: {result['error']}"
    return result.get("formatted_result", "Could not perform calculation.")

# Create the tools using create_from_function
calculator_tool = client.tools.create_from_function(
    func=calculator,
)

# langgraph_tool = client.tools.create_from_function(
#     func=langgraph_calculator,
# )

print(f"Created calculator tool with ID: {calculator_tool.id}")
# print(f"Created LangGraph calculator tool with ID: {langgraph_tool.id}")

# Create a simple agent that uses the calculator tools
agent = client.agents.create(
    name=f"Calculator_Assistant_{unique_suffix}",  # Add unique suffix to agent name too
    description="An assistant that can perform mathematical calculations",
    system="You are a helpful calculator assistant. Use the calculator tool for simple operations and the langgraph_calculator tool for more complex calculations.",
    memory_blocks=[],
    tool_ids=[calculator_tool.id]
)

print(f"Created calculator agent with ID: {agent.id}")
print("Tools:", [t.name for t in agent.tools])