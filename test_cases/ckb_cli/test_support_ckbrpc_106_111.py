from framework.helper.ckb_cli import *
from framework.helper.miner import make_tip_height_number
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestCkbCliSupport110:

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315)
        cls.node.prepare()
        cls.node.start()
        make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_version(self):
        ckb_cli_version = version()
        assert "ckb-cli" in ckb_cli_version, "{ckb_cli_version} not contains ckb-cli".format(
            ckb_cli_version=ckb_cli_version)

    def test_estimate_cycles(self):
        """
        estimate_cycles cellbase tx
        - return : 0
        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        # cast TransactionView to Transaction
        del block['transactions'][0]['hash']

        with open("/tmp/tmp.json", 'w') as tmp_file:
            tmp_file.write(json.dumps(block['transactions'][0]))
        result = estimate_cycles("/tmp/tmp.json",
                                 api_url=self.node.getClient().url)
        assert result == 0

    def test_get_transaction_and_witness_proof(self):
        """
        get_transaction_and_witness_proof cellbase tx
        Returns: block_hash which transactions in the block with this hash

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        cellbase_tx_hash = str(block['transactions'][0]['hash'])
        cellbase_block_hash = block['header']['hash']
        result = get_transaction_and_witness_proof(tx_hashes=cellbase_tx_hash,
                                                   block_hash=None,
                                                   api_url=self.node.getClient().url)
        assert result['block_hash'] == cellbase_block_hash

    def test_verify_transaction_and_witness_proof(self):
        """
        verify_transaction_and_witness_proof cellbase tx_proof
        Returns: cellbase transaction hashes it commits to.

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        tx_proof = self.node.getClient().get_transaction_and_witness_proof(tx_hashes=[block['transactions'][0]['hash']])
        with open("/tmp/tmp.json", 'w') as tmp_file:
            print(f"tx_proof:{tx_proof}")
            tmp_file.write(json.dumps(tx_proof))
        result = verify_transaction_and_witness_proof("/tmp/tmp.json", api_url=self.node.getClient().url)
        assert result == block['transactions'][0]['hash']

    def test_get_block_with_cycles(self):
        """
        get_block_with_cycles for cellbase
        Returns:cycles: []

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        cellbase_block_hash = block['header']['hash']
        result = get_block(cellbase_block_hash, with_cycles=True, api_url=self.node.getClient().url)
        assert result == '[]'

    def test_get_block_by_number_with_cycles(self):
        """
        get_block_by_number_with_cycles for cellbase
        Returns:cycles: []

        """
        block_number = self.node.getClient().get_tip_block_number()
        result = get_block_by_number(block_number, with_cycles=True, api_url=self.node.getClient().url)
        assert result == '[]'

    def test_get_consensus(self):
        """
        get_consensus
        Returns:hardfork_features includes 0048 && 0049

        """
        hardfork_features = get_consensus(api_url=self.node.getClient().url)
        assert any(feature.get('rfc') == '0048' for sublist in hardfork_features for feature in sublist), "不包含 RFC 协议 0048"
        assert any(feature.get('rfc') == '0049' for sublist in hardfork_features for feature in sublist), "不包含 RFC 协议 0049"

    def test_get_deployments_info(self):
        """
        get_deployments_info
        Returns:deployments::light_client::state

        """
        result = get_deployments_info(api_url=self.node.getClient().url)
        assert result["light_client"]["state"] == 'active'
