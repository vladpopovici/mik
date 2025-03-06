import simplejson as json
import numpy as np

class NpJSONEncoder(json.JSONEncoder):
    """Provides an encoder for Numpy types for serialization."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return super().default(obj)
##