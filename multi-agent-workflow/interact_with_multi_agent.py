import json
import datetime
import argparse
from pathlib import Path
from letta_client import Letta

def send_message_to_supervisor(client, supervisor_id, message, worker_ids=None):
    """
    Send a message to the supervisor agent and include worker IDs if provided
    
    Args:
        client: Letta client instance
        supervisor_id: ID of the supervisor agent
        message: Message to send to the supervisor
        worker_ids: Optional list of worker agent IDs to mention in the message
    
    Returns:
        Response from the supervisor agent
    """
    if worker_ids:
        formatted_message = f"{message} Please coordinate with these specific worker agents: {', '.join(worker_ids)} to complete this task. Check with all workers without asking me any follow up questions."
    else:
        formatted_message = message
    
    response = client.agents.messages.create(
        agent_id=supervisor_id,
        messages=[
            {
                "role": "user",
                "content": formatted_message
            }
        ]
    )
    
    return response

def log_agent_interaction(client, supervisor_id, worker_ids, log_file_path="letta_agent_interaction.txt"):
    """
    Dynamically create a detailed log of all agent interactions in a pretty-printed format.
    
    Args:
        client: Letta client instance
        supervisor_id: ID of the supervisor agent
        worker_ids: List of worker agent IDs
        log_file_path: Path where the log file will be saved
    """
    try:
        # Retrieve messages for all agents
        supervisor_messages = client.agents.messages.list(agent_id=supervisor_id)
        worker_messages_list = [client.agents.messages.list(agent_id=worker_id) for worker_id in worker_ids]
        
        # Get shared memory block
        shared_blocks = client.blocks.list()
        team_tasks_block = next((block for block in shared_blocks if block.label == "team_tasks"), None)
        
        # Start writing to log file
        with open(log_file_path, 'w') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("LETTA MULTI-AGENT SYSTEM INTERACTION LOG\n")
            f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # System Overview
            f.write("SYSTEM CONFIGURATION\n")
            f.write("-" * 50 + "\n")
            f.write(f"Supervisor Agent ID: {supervisor_id}\n")
            f.write("Worker Agent IDs:\n")
            for i, worker_id in enumerate(worker_ids):
                f.write(f"  - Worker {i}: {worker_id}\n")
            f.write("\n")
            
            # Shared Memory Blocks
            if team_tasks_block:
                f.write("SHARED MEMORY - TEAM TASKS\n")
                f.write("-" * 50 + "\n")
                try:
                    # Pretty-print the JSON content
                    tasks_json = json.loads(team_tasks_block.value)
                    f.write(json.dumps(tasks_json, indent=2) + "\n\n")
                except json.JSONDecodeError:
                    f.write(team_tasks_block.value + "\n\n")
            
            # Supervisor Agent Interactions
            f.write("SUPERVISOR AGENT ACTIVITY\n")
            f.write("-" * 50 + "\n")
            for msg in supervisor_messages:
                # Skip internal system messages
                if msg.message_type == "user_message" and "heartbeat" in getattr(msg, "content", ""):
                    continue
                
                # Format timestamp
                timestamp = msg.date.strftime('%Y-%m-%d %H:%M:%S')
                
                # Message header based on type
                if msg.message_type == "user_message":
                    f.write(f"\n[{timestamp}] USER → SUPERVISOR\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{msg.content}\n")
                
                elif msg.message_type == "assistant_message":
                    f.write(f"\n[{timestamp}] SUPERVISOR → USER\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{msg.content}\n")
                
                elif msg.message_type == "reasoning_message":
                    f.write(f"\n[{timestamp}] SUPERVISOR REASONING\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{msg.reasoning}\n")
                
                elif msg.message_type == "tool_call_message":
                    f.write(f"\n[{timestamp}] SUPERVISOR TOOL CALL: {msg.tool_call.name}\n")
                    f.write("-" * 30 + "\n")
                    try:
                        # Try to pretty-print the JSON arguments
                        args = json.loads(msg.tool_call.arguments)
                        f.write(json.dumps(args, indent=2) + "\n")
                    except json.JSONDecodeError:
                        f.write(f"{msg.tool_call.arguments}\n")
                
                elif msg.message_type == "tool_return_message":
                    f.write(f"\n[{timestamp}] TOOL RETURN: {msg.status}\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{msg.tool_return}\n")
            
            # Worker Agent Interactions
            for i, worker_messages in enumerate(worker_messages_list):
                worker_id = worker_ids[i]
                f.write("\n\n" + "=" * 50 + "\n")
                f.write(f"WORKER {i} ACTIVITY (ID: {worker_id})\n")
                f.write("=" * 50 + "\n")
                
                for msg in worker_messages:
                    # Skip internal system messages and initial bootup
                    if (msg.message_type == "user_message" and "login" in getattr(msg, "content", "")) or \
                       (msg.message_type == "assistant_message" and "More human than human" in getattr(msg, "content", "")):
                        continue
                    
                    # Format timestamp
                    timestamp = msg.date.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Message header based on type
                    if msg.message_type == "system_message":
                        f.write(f"\n[{timestamp}] SYSTEM → WORKER {i}\n")
                        f.write("-" * 30 + "\n")
                        # Only include the core prompt without memory details
                        prompt_lines = msg.content.split('\n')
                        core_prompt = []
                        for line in prompt_lines:
                            if "### Memory" in line:
                                break
                            core_prompt.append(line)
                        f.write('\n'.join(core_prompt) + "\n")
                    
                    elif msg.message_type == "user_message":
                        f.write(f"\n[{timestamp}] USER/SUPERVISOR → WORKER {i}\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"{msg.content}\n")
                    
                    elif msg.message_type == "assistant_message":
                        f.write(f"\n[{timestamp}] WORKER {i} RESPONSE\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"{msg.content}\n")
                    
                    elif msg.message_type == "reasoning_message":
                        f.write(f"\n[{timestamp}] WORKER {i} REASONING\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"{msg.reasoning}\n")
                    
                    elif msg.message_type == "tool_call_message":
                        f.write(f"\n[{timestamp}] WORKER {i} TOOL CALL: {msg.tool_call.name}\n")
                        f.write("-" * 30 + "\n")
                        try:
                            args = json.loads(msg.tool_call.arguments)
                            f.write(json.dumps(args, indent=2) + "\n")
                        except json.JSONDecodeError:
                            f.write(f"{msg.tool_call.arguments}\n")
            
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("END OF LOG\n")
            f.write("=" * 80 + "\n")
        
        print(f"Agent interaction log successfully saved to {log_file_path}")
        return True
        
    except Exception as e:
        print(f"Error creating agent interaction log: {str(e)}")
        return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Interact with a Letta multi-agent system and generate logs.')
    
    # Add arguments
    parser.add_argument('--server', type=str, default='http://localhost:8283', 
                        help='Letta server URL (default: http://localhost:8283)')
    parser.add_argument('--supervisor', type=str, required=True,
                        help='Supervisor agent ID')
    parser.add_argument('--workers', type=str, nargs='+', required=True,
                        help='Worker agent IDs (space-separated)')
    parser.add_argument('--message', type=str,
                        help='Message to send to the supervisor agent')
    parser.add_argument('--output', type=str, default='letta_multi_agent_log.txt',
                        help='Output log file path (default: letta_multi_agent_log.txt)')
    parser.add_argument('--interactive', action='store_true',
                        help='Enable interactive mode for continuous messaging')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Connect to Letta server
    print(f"Connecting to Letta server at {args.server}...")
    client = Letta(base_url=args.server)
    
    if args.interactive:
        # Interactive mode
        print("\n=== Interactive Mode ===")
        print("Type 'exit' or 'quit' to end the session")
        print("Type 'log' to generate the log file at any time")
        
        while True:
            user_input = input("\nEnter message to send to supervisor (or command): ")
            
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'log':
                log_agent_interaction(
                    client=client,
                    supervisor_id=args.supervisor,
                    worker_ids=args.workers,
                    log_file_path=args.output
                )
                continue
            
            # Send message to supervisor
            print("Sending message to supervisor...")
            response = send_message_to_supervisor(
                client=client,
                supervisor_id=args.supervisor,
                message=user_input,
                worker_ids=args.workers
            )
            
            print("\nSupervisor response:")
            # Handle tuple response structure
            if isinstance(response, tuple) and len(response) >= 2:
                messages = response[1]
                for msg in messages:
                    if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                        print(f"\n{msg.content}")
            else:
                print(f"\nUnexpected response format: {type(response)}")
                print(f"Response: {response}")
            
            # Always log after each interaction in interactive mode
            log_agent_interaction(
                client=client,
                supervisor_id=args.supervisor,
                worker_ids=args.workers,
                log_file_path=args.output
            )
    
    elif args.message:
        # Single message mode
        print(f"Sending message to supervisor: {args.message}")
        response = send_message_to_supervisor(
            client=client,
            supervisor_id=args.supervisor,
            message=args.message,
            worker_ids=args.workers
        )
        
        print("\nSupervisor response:")
        # Handle tuple response structure
        if isinstance(response, tuple) and len(response) >= 2:
            messages = response[1]
            for msg in messages:
                if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                    print(f"\n{msg.content}")
        else:
            print(f"\nUnexpected response format: {type(response)}")
            print(f"Response: {response}")
        
        # Wait a moment for agents to process
        print("\nWaiting for agents to process messages...")
        import time
        time.sleep(5)  # Give agents time to process and respond
        
        # Generate the log
        log_agent_interaction(
            client=client,
            supervisor_id=args.supervisor,
            worker_ids=args.workers,
            log_file_path=args.output
        )
    
    else:
        # Just generate logs mode
        print("Generating logs of existing agent interactions...")
        log_agent_interaction(
            client=client,
            supervisor_id=args.supervisor,
            worker_ids=args.workers,
            log_file_path=args.output
        )

if __name__ == "__main__":
    main()