from typing import Callable, Dict, Any

class FeedbackChannel:
    def __init__(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Initialize the FeedbackChannel with a feedback handler.
        
        Parameters:
            handler (Callable[[Dict[str, Any]], None]): Callable invoked for each feedback message. It must accept a dict describing the feedback (e.g., {"command": ..., "value": ...}); its return value is ignored.
        """
        self.handler = handler

    def receive_feedback(self, feedback_msg: Dict[str, Any]):
        """
        Forward the given feedback message to the configured handler.
        
        Parameters:
            feedback_msg (Dict[str, Any]): Feedback payload to be processed by the handler; its expected keys/values are determined by the handler's contract.
        """
        self.handler(feedback_msg)

# Example handler for an agent
def agent_feedback_handler(msg):
    # Update agent state or behavior based on feedback
    """
    Handle a feedback message for an agent.
    
    Process a feedback payload (a mapping of commands, parameters, or observations) intended to update the agent's state or behavior. The default implementation prints the message; replace or extend this handler to apply the actual changes to the agent.
    
    Parameters:
        msg (dict): Feedback payload (e.g., {"command": "adjust_param", "value": 42}).
    """
    print(f"Received feedback: {msg}")
    # ...apply changes...

# Usage:
# feedback_channel = FeedbackChannel(agent_feedback_handler)
# feedback_channel.receive_feedback({"command": "adjust_param", "value": 42})
