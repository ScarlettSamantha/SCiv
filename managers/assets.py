from typing import Dict, List


class tagTracker:
    def __init__(self):
        # Key is the tag, value is a list of objects with that tag
        self.tags: Dict[str, List[object]] = {}
        
    def add(self, tag: str, instance: object):
        if tag not in self.tags:
            self.tags[tag] = []
        self.tags[tag].append(instance)
        
    def get(self, tag: str) -> List[object]:
        return self.tags[tag]
    
