import json
from typing import Iterator, Dict, Any

class ScenarioRecorder:
    def __init__(self, log_file: str):
        """
        Initialize the instance with the path to the newline-delimited JSON log file.
        
        Parameters:
            log_file (str): Filesystem path to the log file used for recording or replaying events.
        """
        self.log_file = log_file

    def record_event(self, event: Dict[str, Any]):
        """
        Append an event as a single newline-delimited JSON entry to the recorder's log file.
        
        Serializes `event` to JSON and writes it as one line (followed by a newline) to the file path stored in `self.log_file`. This method has the side effect of appending to the file; it does not return a value. File I/O or JSON serialization errors may propagate to the caller.
        
        Parameters:
            event (Dict[str, Any]): Mapping containing the event data to be serialized and recorded.
        """
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

class ScenarioReplayer:
    def __init__(self, log_file: str):
        """
        Initialize the instance with the path to the newline-delimited JSON log file.
        
        Parameters:
            log_file (str): Filesystem path to the log file used for recording or replaying events.
        """
        self.log_file = log_file

    def replay(self, filter_fn=None) -> Iterator[Dict[str, Any]]:
        """
        Yield events from the newline-delimited JSON log file, optionally filtered.
        
        Reads self.log_file line-by-line, parses each line as JSON into a dict, and yields each event.
        If filter_fn is provided, only yields events for which filter_fn(event) returns True.
        
        Parameters:
            filter_fn (Callable[[Dict[str, Any]], bool], optional): A predicate that takes an event dict and
                returns True to include the event, False to skip it. If None, all events are yielded.
        
        Returns:
            Iterator[Dict[str, Any]]: An iterator that yields parsed event dictionaries from the log file.
        """
        with open(self.log_file, "r") as f:
            for line in f:
                event = json.loads(line)
                if filter_fn is None or filter_fn(event):
                    yield event

# Usage:
# recorder = ScenarioRecorder("agent_events.log")
# recorder.record_event(event_dict)
# 
# replayer = ScenarioReplayer("agent_events.log")
# for event in replayer.replay():
#     process_event(event)
