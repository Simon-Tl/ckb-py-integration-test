from framework.helper.miner import make_tip_height_number, miner_with_version
from framework.helper.node import wait_cluster_height, wait_node_height
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestMainNetSoftForkSuccessful:
    @classmethod
    def setup_class(cls):
        node1 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V110_MAIN, "tx_pool_main/node1", 8119,
                                         8227)
        node2 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V110_MAIN, "tx_pool_main/node2", 8120, 8228)
        cls.cluster = Cluster([node1, node2])

        cls.cluster = Cluster([node1, node2])
        cls.node = node1
        cls.node109 = node2

        node1.prepare(other_ckb_config={'ckb_logger_filter': 'debug'},
                      other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})
        node2.prepare(other_ckb_config={'ckb_logger_filter': 'debug'},
                      other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})

        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        make_tip_height_number(node2, 200)
        wait_cluster_height(cls.cluster, 100, 300)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_miner_use_110(self):
        """
        110 node miner will cause softfork active
        1. 110 node miner to 8314
            node.state == defined
        2. 110 node miner to 8315
            node.state == started
        3. 110 node miner to 8356
            node.state == started
        4. 110 node miner to 8567
            node.state == locked_in
        5. 110 node miner to 8650
            node.state == locked_in
        6. 110 node miner to 8651
            node.state == active
        :return:
        """
        make_tip_height_number(self.node, 8314)
        wait_node_height(self.node, 8314, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "defined"
        make_tip_height_number(self.node, 8315)
        wait_node_height(self.node, 8315, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "started"
        make_tip_height_number(self.node, 8356)
        wait_node_height(self.node, 8356, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "started"
        make_tip_height_number(self.node, 8567)
        wait_node_height(self.node, 8567, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "locked_in"
        make_tip_height_number(self.node, 8650)
        wait_node_height(self.node, 8650, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "locked_in"
        make_tip_height_number(self.node, 8651)
        wait_node_height(self.node, 8651, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "active"
        make_tip_height_number(self.node, 8655)
        wait_cluster_height(self.cluster, 8654, 100)
