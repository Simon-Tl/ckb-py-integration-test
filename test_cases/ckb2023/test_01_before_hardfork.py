import pytest

from framework.basic import CkbTest


class TestBeforeHardFork(CkbTest):
    """
    test cases before ckb2023
    """

    cluster: CkbTest.Cluster

    @classmethod
    def setup_class(cls):
        """
        1. start 4 ckb node in tmp/cluster/hardfork/node dir
        2. link ckb node each other
        3. deploy contract
        4. miner 850 block
        :return:
        """
        # 1. start 4 ckb node in tmp/cluster/hardfork/node dir
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST,
                                         f"cluster/hardfork/node{i}",
                                         8114 + i,
                                         8225 + i)
            for
            i in range(1, 5)
        ]
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()

        # 2. link ckb node each other
        cls.cluster.connected_all_nodes()

        # 3. deploy contract
        contracts = cls.Contract_util.deploy_contracts(cls.Config.ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]

        # 4. miner 850 block
        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 850)
        cls.Node.wait_cluster_height(cls.cluster, 850, 100)

    @classmethod
    def teardown_class(cls):
        """
        stop ckb node
        clean ckb node  tmp dir
        :return:
        """
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def setup_method(self, method):
        """
        1. check  that the current CKB2023 are not activated yet.
        :param method:
        :return:
        """
        super().setup_method(method)

        # 1. check that the current CKB2023 are not activated yet.
        current_epoch_result = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        # current epoch <  consensus epoch .length
        assert int(current_epoch_result['number'].replace("0x", "")) \
               < get_epoch_number_by_consensus_response(
            consensus_response, '0048')

    def test_01_rfc_0048_in_consensus(self):
        """
        1. Check if the consensus response  includes RFC 0048
        -  it includes.
        :return:
        """

        # 1. Check if the consensus response  includes RFC 0048
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, "0048")
        assert epoch_number >= 0

    def test_02_rfc_0049_in_consensus(self):
        """
        1. Check if the consensus response  includes RFC 0049
        -  it includes.
        :return:
        """

        # 1. Check if the consensus response  includes RFC 0049
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049')
        assert epoch_number >= 0

    def test_03_0048_miner_with_0x0(self):
        """
        Before the fork, the miner's block version is 0x0.
        1. miner version:0x0 block
        - block mining successful.
        :return:
        """

        # 1. miner version is "0x0" block
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_04_0048_miner_with_0x1(self):
        """
        Before the fork, the miner's block version is 0x1. will return BlockVersionError
        1. miner version is "0x1" block
        - Return error : BlockVersionError
        :return:
        """
        # 1. miner version is "0x1" block
        with pytest.raises(Exception) as exc_info:
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x1")
        expected_error_message = "BlockVersionError"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}" \
            f"' not found in actual string '{exc_info.value.args[0]}'"

    def test_05_0049_transfer_to_data2_address(self):
        """
        Before the fork, send a transaction with type: data2 will return error
        1. check account1 have enough money
            account1_capacity > 0
        2. send capacity to data2 address
        - return error : "the feature \"VM Version 2\" is used in current transaction
                            but not enabled in current chain"
        :return:
        """
        # 1. check account1 have enough money
        account1 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account1_capacity = self.Ckb_cli.wallet_get_capacity(account1['address']['testnet'],
                                                             self.cluster.ckb_nodes[0].client.url)
        assert account1_capacity > 0

        # 2. send capacity to data2 address
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0
        with pytest.raises(Exception) as exc_info:
            self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.ACCOUNT_PRIVATE_1,
                "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
                140,
                self.cluster.ckb_nodes[0].client.url)
        print(exc_info)
        expected_error_message = "the feature \"VM Version 2\" is used in current transaction, but not enabled in current chain"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}'" \
            f" not found in actual string '{exc_info.value.args[0]}'"

    def test_06_0050_invoke_spawn_use_type(self):
        """
        Before the fork, send a transaction contains spawn , use  script:type invoke it. will return error
        1. invoke spawn contrat
        - return error: InvalidEcall(2101)
        :return:
        """

        # 1. invoke spawn contrat
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            tip_block_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
            print('tip_block_number:', tip_block_number)
            tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1,
                                                        code_tx_hash,
                                                        code_tx_index,
                                                        invoke_arg,
                                                        "type",
                                                        invoke_data,
                                                        api_url=self.cluster.ckb_nodes[0].getClient().url)
            print("tx hash :", tx_hash)
        expected_error_message = "InvalidEcall(2101)"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

    def test_07_0049_transfer_tx_when_10th_block_before_fork(self):
        """
        send data2 Transactions  of the 10th block before the fork,the tx status will be rejected or unknown
        1. miner until  the 10th block before the fork
        2. sending data2 returns the transaction hash.
        3. querying the transaction status shows it as rejected or unknown.
        :return:
        """

        # 1. miner until  the 10th block before the fork
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049') * 1000

        self.Miner.make_tip_height_number(self.cluster.ckb_nodes[0], epoch_number - 10)
        self.Node.wait_cluster_height(self.cluster, epoch_number - 10, 100)

        # 2. sending data2 returns the transaction hash.
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.MINER_PRIVATE_1,
            "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
            140,
            self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash}")

        # 3. querying the transaction status shows it as rejected or unknown.
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == "rejected" \
               or tx_response['tx_status']['status'] == "unknown"

    def test_08_send_transfer_tx_when_10th_block_before_fork(self):
        """
        send transfer Transactions  of the 10th block before the fork:
        - return hash
        - Within 10 blocks before and after the fork,
                the transaction status is queried as: unknown.
        - After waiting for +10 blocks after the fork,
                the transaction  can be committed on the blockchain.

        1. miner until  the 10th block before the fork
        2. sending data2 returns the transaction hash.
        3. querying the transaction status shows it as rejected or unknown.
        4. miner until the 20th block after the fork
        5. querying the transaction status shows it as committed,committed number > 10th after fork
        :return:
        """

        # 1. miner until  the 10th block before the fork
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049') * 1000

        self.Miner.make_tip_height_number(self.cluster.ckb_nodes[0], epoch_number - 10)
        self.Node.wait_cluster_height(self.cluster, epoch_number - 10, 100)

        # 2. sending data2 returns the transaction hash.
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0
        account = self.Ckb_cli.util_key_info_by_private_key(account_private=self.Config.ACCOUNT_PRIVATE_2)
        tx_hash1 = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            140,
            self.cluster.ckb_nodes[0].client.url)
        tx_hash2 = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2,
            "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
            140,
            self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash1}")

        # 3. querying the transaction status shows it as rejected or unknown.
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], '0x0')
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash1)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == 'unknown'

        # 4. miner until the 20th block after the fork
        for _ in range(30):
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], '0x0')

        # 5. querying the transaction status shows it as committed,committed number > 10th after fork
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash1)
        print(f"tx response:{tx_response['tx_status']['status']}")
        block = self.cluster.ckb_nodes[0]. \
            getClient(). \
            get_block(tx_response['tx_status']['block_hash'])
        print(int(block["header"]["number"], 16))
        assert int(block["header"]["number"], 16) >= 1010
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash2)
        assert tx_response['tx_status']['status'] == 'committed'


def get_epoch_number_by_consensus_response(consensus_response, rfc_name):
    """
    get ckb epoch number
    "hardfork_features": [
            { "rfc": "0028", "epoch_number": "0x1526" },
         ]
    Example:
    get_epoch_number_by_consensus_response(consensus_response,"0028")
    return int(0x1526,16)
    :param consensus_response:  rpc get_consensus response
    :param rfc_name: example : 0048
    :return:
    """
    hardfork_features = consensus_response['hardfork_features']
    return int(list(filter(lambda obj: rfc_name in obj['rfc'], hardfork_features))[0][
                   'epoch_number'].replace("0x", ""), 16)
