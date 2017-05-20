from WeakCoinProtocol import WeakCoinProtocol


class MeshcashWeakCoinProtocol(WeakCoinProtocol):
    def __init__(self):
        WeakCoinProtocol.__init__(self)

    def output_coin(self, fresh_blocks):
        """
        Output the coin based on the LSB of the minimal freshly-generated blocks
        :param fresh_blocks:
        :return:
        """
        if len(fresh_blocks) == 0:
            raise Exception("No fresh blocks! Cannot compute the value of the weak coin")

        return True if min([block.pow for block in fresh_blocks]) & 1 == 1 else 0
