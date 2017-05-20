import PoWProtocol


class NaivePoWProtocol(PoWProtocol):
    """
    Counts up to 5000 before declaring a successful proofs-of-work.
    """

    def __init__(self):
        self.difficulty = 5000

    def try_single_nonce(self):
        """
        Tries a single nonce
        Returns a tuple of (status, result) where status is True if the nonce is valid and result contains the nonce.
        :return:
        """
        self.lastNonce += 1

        if self.lastNonce == self.difficulty:
            return True, self.lastNonce
        else:
            return False, self.lastNonce

    def verify_pow(self, proof):
        """
        Return the whether the block's proofs-of-work is valid w.r.t difficulty and the current challenge
        :param proof:
        :return:
        """
        return self.lastNonce == self.difficulty

    def adjust_difficulty(self, mesh):
        """
        Adjust the difficulty (for this naive case, does nothing)
        :param mesh:
        :return:
        """
        # Do nothing
        pass
