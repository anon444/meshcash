class HareProtocol:
    def __init__(self):
        # Mapping of recent blocks to their margins (sum of votes for and against)
        self.recentBlocksOpinions = {}

        # The layer in which consensus interval starts (difference from the current layer)
        self.consensusIntervalStart = 2

        # The layer in which consensus interval ends (difference from the current layer)
        self.consensusIntervalEnd = 1

    def get_valid_blocks(self, new_block):
        """
        Return the valid subset of recent blocks based on newBlock's view
        :param new_block:
        :return:
        """
        raise NotImplementedError("Hare protocols should inherit from this class and implement this method")
