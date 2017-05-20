class PoWProtocol:
    """
    A stateful proofs-of-work interface
    """

    def __init__(self):
        # 1/Difficulty is the probability of finding a solution in a single trial
        self.difficulty = 5000

        # Challenge string for the proofs-of-work
        self.challenge = None

        # Last attempted nonce
        self.lastNonce = 0

    def set_challenge(self, challenge):
        """
        Sets the challenge
        :param challenge:
        :return:
        """
        if challenge != self.challenge:
            # Change the challenge
            self.challenge = challenge

            # Reset nonce
            self.lastNonce = 0

    def try_single_nonce(self):
        """
        Tries a single nonce
        Returns a tuple of (status, result) where status is True if the nonce is valid and result contains the nonce.
        :return:
        """
        self.lastNonce += 1
        return True, self.lastNonce

    def verify_pow(self, proof):
        """
        Return the whether the block's proofs-of-work is valid w.r.t difficulty and the current challenge
        :param proof:
        :return:
        """
        return True

    def adjust_difficulty(self, mesh):
        pass
