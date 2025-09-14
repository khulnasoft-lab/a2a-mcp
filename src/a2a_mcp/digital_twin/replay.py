import json
from typing import Iterator, Dict, Any

class ScenarioRecorder:
    def __init__(self, log_file: str):
        """
        Initialize the instance with the path to the JSON-lines log file.
        
        Parameters:
            log_file (str): Filesystem path to the log file used for appending (recorder) or reading (replayer). The path is stored as-is; no validation or I/O occurs during initialization.
        """
        self.log_file = log_file

    def record_event(self, event: Dict[str, Any]):
        """
        Append an event dictionary to the recorder's log file as a single JSON line.
        
        The provided `event` is JSON-serialized and written (with a trailing newline) to `self.log_file` opened in text append mode. This performs a filesystem write and does not return a value.
        
        Parameters:
            event (Dict[str, Any]): The event data to record; must be JSON-serializable.
        """
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

class ScenarioReplayer:
    def __init__(self, log_file: str):
        """
        Initialize the instance with the path to the JSON-lines log file.
        
        Parameters:
            log_file (str): Filesystem path to the log file used for appending (recorder) or reading (replayer). The path is stored as-is; no validation or I/O occurs during initialization.
        """
        self.log_file = log_file

    def replay(self, filter_fn=None) -> Iterator[Dict[str, Any]]:
        """
        Iterate over events stored as JSON Lines in the recorder log, yielding each event dictionary.
        
        Reads the log file line-by-line, parses each line as JSON to produce an event dict, and yields events that pass the optional filter. Processing is lazy (events are produced as the file is read).
        
        Parameters:
            filter_fn (Optional[Callable[[Dict[str, Any]], bool]]): If provided, a predicate applied to each event;
                only events for which `filter_fn(event)` returns True are yielded.
        
        Returns:
            Iterator[Dict[str, Any]]: An iterator that yields event dictionaries parsed from each JSON line in the log.
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
