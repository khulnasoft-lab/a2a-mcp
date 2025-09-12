from typing import Callable, Dict, Any

class FeedbackChannel:
    def __init__(self, handler: Callable[[Dict[str, Any]], None]):
        self.handler = handler

    def receive_feedback(self, feedback_msg: Dict[str, Any]):
        self.handler(feedback_msg)

# Example handler for an agent
def agent_feedback_handler(msg):
    # Update agent state or behavior based on feedback
    print(f"Received feedback: {msg}")
    # ...apply changes...

# Usage:
# feedback_channel = FeedbackChannel(agent_feedback_handler)
# feedback_channel.receive_feedback({"command": "adjust_param", "value": 42})
