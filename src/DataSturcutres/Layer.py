class Layer:
    """
    A layer is a collection of blocks corresponding to a sequential id
    """
    def __init__(self, layer_id, start_layer_ts):
        # Layer id (zero based and sequential)
        self.id = layer_id

        # A Unix timestamp representing the start of the layer
        # This will be later used for Proofs-of-Work difficulty adjustments
        self.start_layer_ts = start_layer_ts

        # The list of blocks claiming their layer to be the current layer
        self.blocks = []
