import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ml.features.feature_definitions import FEATURE_GROUPS

class FeatureRegistry:
    def __init__(self):
        self.groups = FEATURE_GROUPS
        
    def get_all_features(self):
        all_feats = []
        for v in self.groups.values():
            all_feats.extend(v)
        return all_feats
        
    def get_features_by_group(self, group_name):
        return self.groups.get(group_name, [])

# Singleton instance for the system
registry = FeatureRegistry()
