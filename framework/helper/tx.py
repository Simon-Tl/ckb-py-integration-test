from framework.helper.ckb_cli import *
from framework.rpc import RPCClient
import time, random


def send_transfer_self_tx_with_input(input_tx_hash_list, input_tx_index_list, sign_private, data="0x",
                                     fee=5000, output_count=1,
                                     api_url="http://127.0.0.1:8114", dep_cells=[]):
    # tx file init

    tmp_tx_file = f"/tmp/demo{time.time()}-{random.randint(0, 100000000)}.json"
    tx_init(tmp_tx_file, api_url)
    account = util_key_info_by_private_key(sign_private)
    account_address = account["address"]["testnet"]
    tx_add_multisig_config(account_address, tmp_tx_file, api_url)
    # add input
    output_cell_capacity_total = 0
    input_cell_template: any
    for i in range(len(input_tx_hash_list)):
        input_tx_index = input_tx_index_list[i]
        input_tx_hash = input_tx_hash_list[i]
        print(f"input_tx_index:{input_tx_index}")
        tx_add_input(input_tx_hash, int(input_tx_index, 16), tmp_tx_file, api_url)
        # add output
        input_cell = RPCClient(api_url).get_transaction(input_tx_hash)["transaction"]["outputs"][
            int(input_tx_index, 16)]
        output_cell_capacity = int(int(input_cell["capacity"], 16) - fee)
        output_cell_capacity_total += output_cell_capacity
        input_cell_template = input_cell
    min_output_count = min(int(output_cell_capacity_total / (100 * 100000000)), output_count)
    min_output_count = max(min_output_count, 1)
    output_cell_capacity = int(output_cell_capacity_total / min_output_count)
    for i in range(min_output_count):
        tx_add_type_out_put(input_cell_template["lock"]["code_hash"], input_cell_template["lock"]["hash_type"],
                            input_cell_template["lock"]["args"],
                            hex(output_cell_capacity), data, tmp_tx_file, False)
    for i in range(len(dep_cells)):
        tx_add_cell_dep(dep_cells[i]['tx_hash'],dep_cells[i]['index_hex'],tmp_tx_file)

    # sign
    sign_data = tx_sign_inputs(sign_private, tmp_tx_file, api_url)
    tx_add_signature(sign_data[0]['lock-arg'], sign_data[0]['signature'], tmp_tx_file, api_url)
    tx_info(tmp_tx_file, api_url)
    # send tx return hash
    return tx_send(tmp_tx_file, api_url).strip()
