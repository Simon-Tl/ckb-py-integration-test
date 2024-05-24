from framework.basic import CkbTest


class TestMainnetSoftForkWithCkbLightClient(CkbTest):
    node: CkbTest.CkbNode
    cluster: CkbTest.Cluster
    ckb_light_node: CkbTest.CkbLightClientNode

    @classmethod
    def setup_class(cls):
        """
        1. start 2 node
        2. connected 2 node
        3. miner until 200 block
        4. start light node
        5. wait light node sync
        Returns:

        """

        # 1. start 2 node
        node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_main/node1", 8115, 8227
        )
        node2 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_main/node2", 8116, 8228
        )
        cls.node = node1
        cls.cluster = cls.Cluster([node1, node2])
        node1.prepare(
            other_ckb_spec_config={
                "ckb_params_genesis_epoch_length": "1",
                "ckb_name": "ckb",
            }
        )
        node2.prepare(
            other_ckb_spec_config={
                "ckb_params_genesis_epoch_length": "1",
                "ckb_name": "ckb",
            }
        )
        cls.cluster.start_all_nodes()

        # 2. connected 2 node
        cls.cluster.connected_all_nodes()

        # 3. miner until 200 block
        cls.Miner.make_tip_height_number(cls.node, 200)
        cls.Node.wait_cluster_height(cls.cluster, 100, 300)

        # 4. start light node
        cls.ckb_light_node = cls.CkbLightClientNode.init_by_nodes(
            cls.CkbLightClientConfigPath.CURRENT_TEST,
            [cls.node],
            "tx_pool_light/node1",
            8001,
        )

        cls.account = cls.Ckb_cli.util_key_info_by_private_key(
            cls.Config.MINER_PRIVATE_1
        )

        cls.ckb_light_node.prepare()
        cls.ckb_light_node.start()

        # 5. wait light node sync
        cls.ckb_light_node.getClient().set_scripts(
            [
                {
                    "script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": cls.account["lock_arg"],
                    },
                    "script_type": "lock",
                    "block_number": "0x0",
                }
            ],
            "all",
        )
        cls.Node.wait_light_sync_height(cls.ckb_light_node, 100, 200)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop_miner()
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node.stop()
        cls.ckb_light_node.clean()

    def test_01_soft_fork_activation_light_node(self):
        """
        Soft fork transitioning from 'defined' to 'active' will not
        affect the synchronization of light nodes.
        1. Mine until block 10000.
            Successful.
        2. Wait for light nodes to synchronize up to block 10000.
            Successful.
        3. Query the balance of the mining address.
            Light node == node.
        :return:
        """

        # 1. Mine until block 10000.
        self.Miner.make_tip_height_number(self.node, 10000)
        self.Node.wait_cluster_height(self.cluster, 10000, 300)
        height = self.cluster.get_all_nodes_height()
        assert height[0] == height[1]
        node_res = (
            self.cluster.ckb_nodes[0]
            .getClient()
            .get_cells_capacity(
                {
                    "script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": self.account["lock_arg"],
                    },
                    "script_type": "lock",
                }
            )
        )
        self.node.start_miner()

        # 2. Wait for light nodes to synchronize up to block 10000.
        self.Node.wait_light_sync_height(self.ckb_light_node, height[0], 800)

        # 3. Query the balance of the mining address.
        light_res = self.ckb_light_node.getClient().get_cells_capacity(
            {
                "script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account["lock_arg"],
                },
                "script_type": "lock",
            }
        )
        assert int(node_res["capacity"], 16) <= int(light_res["capacity"], 16)
