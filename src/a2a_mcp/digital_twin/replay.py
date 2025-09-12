import json
from typing import Iterator, Dict, Any

class ScenarioRecorder:
    def __init__(self, log_file: str):
        self.log_file = log_file

    def record_event(self, event: Dict[str, Any]):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

class ScenarioReplayer:
    def __init__(self, log_file: str):
        self.log_file = log_file

    def replay(self, filter_fn=None) -> Iterator[Dict[str, Any]]:
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
