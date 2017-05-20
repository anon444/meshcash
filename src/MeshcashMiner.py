import logging
from threading import Timer

from HareProtocols.TrivialHareProtocol import TrivialHareProtocol
from PoW.NaivePoWProtocol import NaivePoWProtocol
from WeakCoin.MeshcashWeakCoinProtocol import MeshcashWeakCoinProtocol
from Transactions.TransactionListenerService import TransactionListenerService


class MeshcashMiner:
    def __init__(self, pk, mesh):
        # The ID of the miner
        # Similarly to Bitcoin, each miner is assigned with a unique public key for identification.
        # Each block contain its miner public key thus entitling him of Coinbase reward.
        self.pk = pk

        # A representation of the BlockDAG as seen by this miner.
        # Mesh will be initialized upon connecting to the network and updated throughout the miner's lifetime.
        self.mesh = mesh

        # The ID of the layer to currently mine on.
        # When successfully mining a block, this will become its corresponding layer ID.
        self.layer_counter = 0

        # The content of the actively mined block.
        # The block object will contain the miner's view and will update with new arriving blocks
        self.current_mined_block = None

        # A Proofs-of-Work interface
        # This is interchangeable and is used to generate and validate PoW solutions.
        self.pow_protocol = NaivePoWProtocol()

        # A flag to indicate whether the block changed since it was last hashed
        # When set, the proofs-of-work interface will restart a solution search over the new block's contents
        self.current_block_changed_flag = False

        # A list of blocks in the miner's view that cannot be reached by existing edges
        # (i.e. blocks with in-degree of 0)
        # This list will be used to recursively "reconstruct" the miner's view
        # for the hare protocol and block validation
        self.current_heads = []

        # A subset of the blocks in the miner's view that the miner votes for
        # These blocks are selected by the hare protocol
        self.voting_edges = []

        # A distributed weak coin protocol interface
        # This is interchangeable and is used to select a bit s.t. honest players agree on its value w.h.p.
        self.weak_coin_protocol = MeshcashWeakCoinProtocol()

        # A list of blocks generated since last layer incrementation
        # In Meshcash, this is used for the weak coin protocol
        self.fresh_blocks = []

        # A (possibly faulty) but quick consensus protocol interface
        # This is interchangeable and is used to get agreement on recently created blocks
        # For ease of read, we use the simpler (majority vote) of two Hare protocols presented in the article.
        self.hare_protocol = TrivialHareProtocol()

        # Length of early block interval in seconds.
        # A bound on the network delay to set this value.
        self.delta_seconds = 30

        # Timer object to decide on whether currently mined block is early
        # This timer will be triggered on every layer, delta seconds after its start
        self.early_block_timer = Timer(self.delta_seconds, self.set_early_block, args=[False])

        # Length of interval in which weak coin is determined.
        self.delta_coin_seconds = 120

        # Timer object to decide on whether currently mined block was created before coin was determined
        # This timer will be triggered on every layer, delta coin seconds after its start
        self.before_coin_timer = Timer(self.delta_coin_seconds, self.set_before_coin)

        # A transaction publish-subscribe service
        # The miner can register for new transactions
        self.tx_listener = TransactionListenerService()

        # Mapping of transaction to first layer id in which they were included
        # This is used to avoid including redeemed transactions
        self.confirmed_txs = {}

        # Transactions that appear in blocks that were received in the current layer
        # This is used to update the mapping of confirmed transactions whenever a layer ends
        # NOTE: this is a heuristic mechanism as some transactions included in the layer might not be confirmed
        # under an attack. We use this implementation for ease of read and assume that an optimized mechanism
        # will include "ancient" unconfirmed transaction based on the Tortoise protocol
        self.newly_confirmed_txs = []

    def mine(self):
        """
        The main loop of the miner and the entry point for the miner.
        The goal of this method is to attempt mining a block while considering newly arriving blocks
         affecting the currently mined block content.
        In an optimized implementation, this would run in on another thread.
        :return:
        """

        # Read the existing mesh
        logging.info("Updating to the latest mesh...")
        self.mesh.initialize()

        # Set the layer counter according to the Mesh last valid layer
        self.layer_counter = self.mesh.get_last_valid_layer()
        logging.info("Setting layer counter to %s", self.layer_counter)

        # Initialize hare protocol opinions about recent blocks
        logging.info("Setting hare protocol opinions about recent layers' blocks")
        self.hare_protocol.set_block_opinions(self.mesh, self.layer_counter)

        # Register for "new arriving blocks" event
        # When a new block arrives, the handle_new_block function will be called
        # to update currently mined block's content
        logging.info("Registering for newly arriving blocks")
        self.mesh.register_for_new_arriving_blocks(self.handle_new_block)

        # Register for "new arriving transactions" event
        # When a new transaction arrives the handle_new_transaction_function will be called
        # the update currently mined block's content
        logging.info("Registering for newly arriving transactions")
        self.tx_listener.register_for_new_arriving_transactions(self.handle_new_transaction)

        # Wait until the start of the next layer to start mining
        # in an optimized implementation, we can start immediately but we would need to handle some special cases
        # (e.g. recognizing freshly-generated blocks when we haven't been around since the start of the layer)
        logging.info("Waiting for the next layer to start mining...")
        current_layer_counter = self.layer_counter
        while self.layer_counter <= current_layer_counter:
            pass

        # Main mining loop
        logging.info("Starting to mine...")
        while True:
            if self.current_block_changed_flag:
                # Compute new PoW challenge
                self.pow_protocol.set_challenge(self.current_mined_block)

                # Challenge is now up-to-date with latest mesh
                self.current_block_changed_flag = False

            success, proof = self.pow_protocol.try_single_nonce()
            if success:
                # Setting the successful proofs-of-work to the currently mined block
                logging.info("Found a successful proofs-of-work for currently mined block!")
                self.current_mined_block.pow = proof

                # Publish currently mined block
                logging.info("Publishing the mined block to the rest of the network")
                self.current_mined_block.publish()

    def handle_new_block(self, new_received_block):
        """
        receives a new block and updates all relevant data structures.
        This is actually the main mining algorithm.
        :param new_received_block:
        :return:
        """
        block_id = new_received_block.generate_block_id()
        logging.debug("Block %s arrived", block_id)

        if not new_received_block.is_syntactically_validity(self.pow_protocol, self.mesh.tmin):
            logging.warning("Block % is syntactically invalid", block_id)
            return

        logging.debug("Recomputing valid recent blocks using the hare protocol")
        self.voting_edges = self.hare_protocol.get_valid_blocks(new_received_block)

        logging.debug("Updating current heads (i.e. blocks with in-degree 0)")
        self.current_heads = self.update_heads(new_received_block)

        logging.debug("Adding % to the list of `fresh` blocks", block_id)
        self.fresh_blocks.append(new_received_block)

        if self.should_update_layer_counter():
            logging.debug("Incrementing layer counter to %s", self.layer_counter + 1)
            self.layer_counter += 1

            logging.debug("Resetting fresh blocks")
            self.fresh_blocks = []

            logging.debug("Set currently mined block 'early block' flag")
            self.set_early_block(True)

            logging.debug("Setting early block timer to change %s seconds from now", self.delta_seconds)
            self.early_block_timer.start()

            logging.debug("Set currently mined block 'before coin' flag")
            self.set_before_coin(True)

            logging.debug("Setting before coin timer to change flag % seconds from now", self.delta_coin_seconds)
            self.before_coin_timer.start()

            # Upon layer incrementation, the last "hare" layer becomes a "tortoise" layer
            # thus its blocks should be removed from hare's blocks' opinions
            logging.debug("Removing opinions about blocks in the last hare protocol layer")
            self.hare_protocol.remove_oldest_layer_from_opinions(self.layer_counter)

            # Remove confirmed transactions from the list of mined transactions
            for newlyConfirmedTransaction in self.newly_confirmed_txs:
                self.confirmed_txs[newlyConfirmedTransaction] = self.layer_counter - 1
                self.current_mined_block.txs.remove(newlyConfirmedTransaction)

        logging.debug("Adjusting proofs-of-work difficulty setting")
        self.pow_protocol.adjust_difficulty(self.mesh)

        print "Updating the current block content based on miner's view"
        self.update_current_block(new_received_block)

        # Setting this flag to alert the proofs-of-work protocol about
        # a change requiring a challenge reset
        self.current_block_changed_flag = True

    def set_early_block(self, val):
        print "Setting `early block`={}".format(val)
        self.current_mined_block.earlyBlock = val

    def set_before_coin(self, val):
        print "Setting `before coin`={}".format(val)
        self.current_mined_block.beforeCoin = val

    def update_heads(self, block):
        """
        add newBlock to current_heads; if newBlock points to a current head, take it out
        :param block:
        :return:
        """
        self.current_heads.append(block)
        return filter(lambda x: x in block.validRecentBlocks, self.current_heads)

    def should_update_layer_counter(self):
        """
        Return True if layer counter should be incremented
        :return:
        """

        # Check if given the newly added block there are at least TMIN blocks
        current_layer_block_count = len(self.mesh.layers[self.layer_counter].blocks) + 1
        return current_layer_block_count >= self.mesh.tmin

    def update_current_block(self, new_received_block):
        """
        Update the content of the currently mined block according to the miner's view and arriving block
        :param new_received_block:
        :return:
        """

        # Set miner's public key
        # NOTE: shouldn't be done on each update but concentrating all hashed values in
        # a single function makes it easier to follow the block's contents
        self.current_mined_block.minerPk = self.pk

        # Set the layer id of the currently mined block by current layer
        self.current_mined_block.layerId = self.layer_counter

        # If the newly arrived block is pointing to a subset of "head block"
        # we remove them from the list of heads (because they are reachable throughout the added block's view)
        self.current_mined_block.viewHeads = set(self.current_heads) - set(new_received_block.validRecentBlocks)

        # Set voting edges according to the hare protocol's output
        self.current_mined_block.votingEdges = self.voting_edges

        # Update the latest value of the weak coin according to the weak coin protocol
        self.current_mined_block.weakCoinValue = self.weak_coin_protocol.output_coin(self.fresh_blocks)

    def handle_new_transaction(self, tx):
        """
        Handle upcoming transactions
        :param tx:
        :return:
        """
        # If this transaction was previously confirmed, there's nothing to do
        if tx in self.confirmed_txs.keys():
            return

        # If this transaction is syntactically invalid, ignore it
        if not tx.is_syntactically_valid():
            return

        # Add the current list of mined transactions
        self.current_mined_block.txs.append(tx)
