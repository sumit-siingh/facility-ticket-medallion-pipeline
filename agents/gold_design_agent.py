import json
from agents.local_llm_agent import LocalLLMAgent


class GoldDesignAgent:
    """
    Uses LLM to propose gold layer models.
    """

    def __init__(self):
        self.llm = LocalLLMAgent()

    def run(self, schema: dict, profile: dict):

        prompt = f"""

        You are a senior analytics engineer.

Business domain:
Facilities management ticketing system.

Tickets are raised by building occupants and assigned to maintenance staff.

Goals:
- Identify operational bottlenecks
- Measure assignee performance
- Measure SLA compliance
- Identify problematic buildings

Given the schema and profile below,
propose 3 gold-layer business tables.

Schema:
{json.dumps(schema, indent=2)}

Data profile:
{json.dumps(profile, indent=2)}

Design 3 gold layer tables:

Return ONLY JSON:
[
  {{
    "name": "",
    "purpose": "",
    "metrics": []
  }}
]
"""

        response = self.llm.ask(prompt)

        return {
            "raw_llm_output": response
        }