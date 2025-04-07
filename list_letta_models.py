from letta_client import Letta

# Connect to your Letta server
client = Letta(base_url="http://localhost:8283")

# List all available LLM models, including Bedrock models
models = client.models.list_llms()
print(models)