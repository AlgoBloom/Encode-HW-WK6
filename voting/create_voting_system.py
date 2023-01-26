# Previously funded account is used to fund new account
# My address: BSTDOSCCPYN3AZNRGBX3VO4XBEAH2TKCGKYZPMYIIRNYAFHJZGNASJMOEI
# My private key: cYGCLpViChb078xonSF43x/IUQvdFlI0jPeD30DZCwIMpjdIQn4bsGWxMG+6u5cJAH1NQjKxl7MIRFuAFOnJmg==
# My passphrase: comfort anxiety nuclear citizen below airport leisure smooth public major rose worth mother stamp tribe bitter medal cotton wink wealth like wagon aware abandon witness

import json
import base64
import contracts
from util import *
from typing import Tuple, List
from algosdk import *
from algosdk.future.transaction import *
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk import constants
from algosdk.v2client.algod import AlgodClient
from algosdk.logic import get_application_address

my_address = "BSTDOSCCPYN3AZNRGBX3VO4XBEAH2TKCGKYZPMYIIRNYAFHJZGNASJMOEI"
pk_1 = "cYGCLpViChb078xonSF43x/IUQvdFlI0jPeD30DZCwIMpjdIQn4bsGWxMG+6u5cJAH1NQjKxl7MIRFuAFOnJmg=="
sk_1 = mnemonic.to_private_key("comfort anxiety nuclear citizen below airport leisure smooth public major rose worth mother stamp tribe bitter medal cotton wink wealth like wagon aware abandon witness")

ALGOD_ADDRESS = "https://testnet-api.algonode.network"
ALGOD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

def getAlgodClient() -> AlgodClient:
    return AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""

def getContracts(client: AlgodClient) -> Tuple[bytes, bytes]:

    global APPROVAL_PROGRAM
    global CLEAR_STATE_PROGRAM

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = fullyCompileContract(client, contracts.approval_program())
        CLEAR_STATE_PROGRAM = fullyCompileContract(client, contracts.clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM

# convert 64 bit integer i to byte string
def intToBytes(i):
    return i.to_bytes(8, "big")

def createApp(
    client,
    sender_addr,
    sender_pk,
    voting_asa,
) -> int:

    approval, clear = getContracts(client)

    globalSchema = transaction.StateSchema(num_uints=6, num_byte_slices=2)
    localSchema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    status = client.status()
    regBegin = status["last-round"] + 10
    regEnd = regBegin + 10
    voteBegin = regEnd + 1
    voteEnd = voteBegin + 10

    app_args = [
        intToBytes(regBegin),
        intToBytes(regEnd),
        intToBytes(voteBegin),
        intToBytes(voteEnd),
        voting_asa,
    ]

    txn = transaction.ApplicationCreateTxn(
        sender=sender_addr,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval,
        clear_program=clear,
        global_schema=globalSchema,
        local_schema=localSchema,
        app_args=app_args,
        sp=client.suggested_params(),
    )

    signedTxn = txn.sign(sender_pk)

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex

#### ASA Application ####

def create_asa(secret_key, my_address):
    algod_address = "https://testnet-api.algonode.network"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)

    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos".format(account_info.get('amount')) + "\n")

    params = algod_client.suggested_params()
    txn = AssetConfigTxn(
        sender=my_address,
        sp=params,
        total=1000000,
        default_frozen=False,
        unit_name="ENB",
        asset_name="Encode Bootcamp Token",
        manager=my_address,
        reserve=my_address,
        freeze=my_address,
        clawback=my_address,
        url="https://path/to/my/asset/details", 
        decimals=0)
    # Sign with secret key of creator
    stxn = txn.sign(secret_key)
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
    except Exception as err:
        print(err)
    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    ptx = algod_client.pending_transaction_info(txid)
    asset_id = ptx["asset-index"]
    return asset_id

#######################
#### Function CALLS ####
#######################
AlgodClient = getAlgodClient()
asa = create_asa(sk_1, my_address)
print(asa)
app = createApp(
    client=AlgodClient,
    sender_addr=my_address,
    sender_pk=pk_1,
    voting_asa=asa,
)
print(app)