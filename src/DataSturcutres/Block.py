class Block:
    """
    A block is the smallest unit of data in Meshcash
    A block includes a list of transactions and knowledge regarding the view of the creating miner
    """
    def __init__(self):
        # The layer of which this block belongs to
        self.layerId = None

        # The public key of this block generating miner
        # This will be used to reward the miner
        self.minerPk = None

        # Binary value of the weak coin protocol
        self.weakCoinValue = None

        # All recent blocks observed by the miner generating this block
        # This list contains only blocks with in-degree 0 (that otherwise wouldn't appear in the recent blocks list)
        self.viewHeads = []

        # Subset of view edges declared valid by the hare protocol
        self.validRecentBlocks = []

        # A flag set to True if the block was created up to t_delta_coin time after layer creation
        # When this flag is turned out the block "abstains" from block voting
        self.beforeCoin = None

        # A flag set to True if the block was created up to delta_time after layer creation
        # When this flag is turned out the block "abstains" from block voting
        self.earlyBlock = None

        # List of included transactions
        self.txs = []

        # Proofs of work over the block contents
        # This serves as a digital signature to assure data was not changed since finding the proofs of work
        self.pow = None

    def has_in_view(self, other_block):
        """
        Returns true if current block points otherBlock
        :param other_block:
        :return:
        """
        if other_block.layerId >= self.layerId:
            return False

        pointed_blocks = set(self.viewHeads).union(set(self.validRecentBlocks))
        if other_block in pointed_blocks:
            return True

        # Very inefficient algorithm
        return max([pointedBlock.has_in_view(other_block) for pointedBlock in pointed_blocks])

    def is_syntactically_valid(self, pow_protocol, tmin):
        """
        Returns True if the block syntactically valid, that is:
        1. recursive: points to TMIN syntactically valid blocks in previous layer AND
        2. has a valid proofs-of-work w.r.t. challenge and difficulty AND
        3. all of its transactions are syntactically valid
        :return:
        """
        if self.layerId == 0:
            # Genesis layer's blocks are always syntactically valid
            return True

        if not pow_protocol.verify_pow(self.pow):
            return False

        prev_layer_blocks = filter(lambda x: x.layerId + 1 == self.layerId, self.viewHeads)
        prev_layer_valid_blocks = sum([block.is_syntactically_valid(pow_protocol) for block in prev_layer_blocks])
        if prev_layer_valid_blocks < tmin:
            # Block must point to at least tmin syntactically valid previous layer's blocks
            return False

        return True

    def generate_block_id(self):
        """
        Return the block's id based on all of its content
        :return:
        """

        # Use the proofs-of-work as the block's id
        return self.pow

