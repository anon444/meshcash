from HareProtocols.HareProtocol import HareProtocol


class TrivialHareProtocol(HareProtocol):
    def __init__(self):
        # Mapping of recent blocks to their margins (sum of votes for and against)
        HareProtocol.__init__(self)
        self.recentBlocksOpinions = {}

        # The layer in which consensus interval starts (difference from the current layer)
        self.consensusIntervalStart = 2

        # The layer in which consensus interval ends (difference from the current layer)
        self.consensusIntervalEnd = 1

    def get_valid_blocks(self, new_block):
        """
        Update opinions about recent blocks
        :param new_block:
        :return:
        """
        for block in self.recentBlocksOpinions.keys():
            if new_block.has_in_view(block):
                self.recentBlocksOpinions[block] += 1
            else:
                self.recentBlocksOpinions[block] -= 1

        # Return a majority vote over recent blocks
        return [k for k, v in self.recentBlocksOpinions.iteritems() if v > 0]

    def set_block_opinions(self, mesh, current_layer):
        pass

    def remove_oldest_layer_from_opinions(self, current_layer):
        """
        Remove blocks from the oldest consensus interval layer
        This will be called upon layer incrementation in which the last consensus interval layer
        transition from the hare protocol to the tortoise
        :param current_layer:
        :return:
        """
        for block in self.recentBlocksOpinions.keys():
            if block.layerId == current_layer - self.consensusIntervalStart:
                del self.recentBlocksOpinions[block]
