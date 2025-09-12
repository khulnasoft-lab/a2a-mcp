from typing import Callable, Dict, Any

class FeedbackChannel:
    def __init__(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Initialize the FeedbackChannel with a feedback handler callback.
        
        Parameters:
            handler (Callable[[Dict[str, Any]], None]): A callback that will be invoked with each feedback
                message (a dict). The handler is responsible for processing the feedback; it may raise
                exceptions which will propagate to the caller.
        """
        self.handler = handler

    def receive_feedback(self, feedback_msg: Dict[str, Any]):
        """
        Forward a feedback message to the configured handler.
        
        The method delegates processing of the provided feedback dictionary to the channel's handler callback.
        Any exceptions raised by the handler propagate to the caller.
        
        Parameters:
            feedback_msg (Dict[str, Any]): A feedback payload describing an event or instruction for the agent (format depends on the handler).
        """
        self.handler(feedback_msg)

# Example handler for an agent
def agent_feedback_handler(msg):
    # Update agent state or behavior based on feedback
    """
    Handle a feedback message for the agent, applying updates to agent state or behavior.
    
    Parameters:
        msg (dict): Feedback payload, typically a mapping of string keys to values (e.g. {"command": "adjust_param", "value": 42}). The function may mutate agent state or trigger actions based on the message contents.
    """
    print(f"Received feedback: {msg}")
    # ...apply changes...

# Usage:
# feedback_channel = FeedbackChannel(agent_feedback_handler)
# feedback_channel.receive_feedback({"command": "adjust_param", "value": 42})
