from framework.basic import CkbTest


class TestGetLiveCell(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/livecell/node1 node dir
        2. miner 100block
        Returns:

        """
        # 1. start 1 ckb node in tmp/feature/gene_rate_epochs node dir
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "livecell/node1", 8120, 8225
        )
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "180_000"})
        cls.node.start()
        # 2. miner 100block
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node  tmp dir
        Returns:

        """
        cls.node.stop()
        cls.node.clean()

    def test_get_live_cell_with_unspend(self):
        """
        1. get cells and tx is pending and with unspend
        2. query cell status will be live
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.MINER_PRIVATE_1,
            account["address"]["testnet"],
            100,
            self.node.getClient().url,
            "1500",
        )
        print(f"txHash:{tx_hash}")
        transaction = self.node.getClient().get_transaction(tx_hash)
        result = self.node.getClient().get_live_cell_with_include_tx_pool(
            transaction["transaction"]["inputs"][0]["previous_output"]["index"],
            transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"],
        )
        assert result["status"] == "live"

    def test_get_live_cell_with_spend(self):
        """
        1. get live cells and cell is spend
        2. query cell status will be unknown
        Returns:

        """
        # 1. generate account and build normal tx
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
            "1500000",
        )
        tx_hash = father_tx_hash
        # 2. send link tx and test_tx_pool_accept check success
        for i in range(3):
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1100090 + i * 1000,
                api_url=self.node.getClient().url,
            )
            self.node.getClient().test_tx_pool_accept(tx, "passthrough")
            self.node.getClient().send_transaction(tx)
            transaction = self.node.getClient().get_transaction(father_tx_hash)
            result = self.node.getClient().get_live_cell_with_include_tx_pool(
                transaction["transaction"]["inputs"][0]["previous_output"]["index"],
                transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"],
                include_tx_pool=True,
            )
            assert result["status"] == "unknown"
