class TransactionListenerService:
    """
    Pub/Sub service for transactions
    """

    def __init__(self):
        pass

    def register_for_new_arriving_transactions(self, handle_new_transaction):
        """
        Adds handle_new_transaction to the subscribers list
         so that it'll be called back upon every new arriving transaction
        :param handle_new_transaction:
        :return:
        """

        # Remains unimplemented at this point
        pass
