from DataSturcutres.Block import Block
from DataSturcutres.Layer import Layer
from datetime import datetime


class Mesh:
    """
    The Mesh object is layered DAG composed of sequential layers
    """

    def __init__(self):
        # Minimal number of blocks in a layer
        self.tmin = 200

        # Create a genesis block
        genesis_layer = Layer(layer_id=0, start_layer_ts=datetime.now())
        self.layers = [genesis_layer]
        for i in range(self.tmin):
            genesis_block = Block()
            genesis_block.layerId = 0
            genesis_layer.blocks.append(genesis_block)

    def get_last_valid_layer(self):
        """
        Returns the last layer valid layer
        :return:
        """
        return self.layers[:-1]

    def register_for_new_arriving_blocks(self, callback_func):
        """
        Call callback_func upon new arriving blocks
        :param callback_func:
        :return:
        """

        # Remains unimplemented at the moment
        pass

    def initialize(self):
        """
        Initialize the mesh contents based on file checkpoints and the gossip network
        :return:
        """

        # Remains unimplemented at the moment
        pass

