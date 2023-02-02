from helper import *
from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod, indexer

import unittest

funding_acct = "BSTDOSCCPYN3AZNRGBX3VO4XBEAH2TKCGKYZPMYIIRNYAFHJZGNASJMOEI"
funding_acct_mnemonic = "comfort anxiety nuclear citizen below airport leisure smooth public major rose worth mother stamp tribe bitter medal cotton wink wealth like wagon aware abandon witness"

algod_address = "https://testnet-api.algonode.cloud"
indexer_address = "https://testnet-idx.algonode.cloud"

# user declared account mnemonics

unittest.TestLoader.sortTestMethodsUsing = None

class TestContract(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.algod_client = algod.AlgodClient("", algod_address)
        cls.algod_indexer = indexer.IndexerClient("", indexer_address)
        cls.funding_acct = funding_acct
        cls.funding_acct_mnemonic = funding_acct_mnemonic
        cls.new_acct_priv_key, cls.new_acct_addr = account.generate_account()
        cls.new_acct_mnemonic = mnemonic.from_private_key(cls.new_acct_priv_key)
        cls.new_acct_addr = account.address_from_private_key(cls.new_acct_priv_key)
        print("Generated new account: "+cls.new_acct_addr)
        cls.app_index = 0
    
    #Methods for test cases must start with test
    def test_app(self):
        amt = 1000000
        fund_new_acct(TestContract.algod_client, TestContract.new_acct_addr, amt, TestContract.funding_acct_mnemonic)   
        print("Funded {amt} to new account for the purpose of deploying contract".format(amt = amt))

        voting_asa = create_asa(TestContract.new_acct_priv_key, TestContract.new_acct_addr) 
        print(f"Deployed voting Fungible Token with ASA id:{voting_asa}")

        creator_private_key = get_private_key_from_mnemonic(TestContract.new_acct_mnemonic)

        # declare application state storage (immutable)
        local_ints = 2
        local_bytes = 2
        global_ints = (
            7
        )
        global_bytes = 2
        global_schema = transaction.StateSchema(global_ints, global_bytes)
        local_schema = transaction.StateSchema(local_ints, local_bytes)

        # get PyTeal approval program
        approval_program_ast = approval_program()
        # compile program to TEAL assembly
        approval_program_teal = compileTeal(
            approval_program_ast, mode=Mode.Application, version=5
        )
        # compile program to binary
        approval_program_compiled = compile_program(TestContract.algod_client, approval_program_teal)

        # get PyTeal clear state program
        clear_state_program_ast = clear_state_program()
        # compile program to TEAL assembly
        clear_state_program_teal = compileTeal(
            clear_state_program_ast, mode=Mode.Application, version=5
        )
        # compile program to binary
        clear_state_program_compiled = compile_program(
            TestContract.algod_client, clear_state_program_teal
        )

        # configure registration and voting period
        status = TestContract.algod_client.status()
        regBegin = status["last-round"]
        regEnd = regBegin + 100000
        voteBegin = status["last-round"]
        voteEnd = voteBegin + 100000
        voting_asa = voting_asa

        print(f"Registration rounds: {regBegin} to {regEnd}")
        print(f"Vote rounds: {voteBegin} to {voteEnd}")

        # create list of bytes for app args
        app_args = [
            intToBytes(regBegin),
            intToBytes(regEnd),
            intToBytes(voteBegin),
            intToBytes(voteEnd),
            # need to store the voting token address in global state
            # intToBytes(voting_asa),
        ]
        
        # create new application
        TestContract.app_index = create_app(
            TestContract.algod_client,
            creator_private_key,
            approval_program_compiled,
            clear_state_program_compiled,
            global_schema,
            local_schema,
            app_args,
            [voting_asa],
        )

        new_app_id = TestContract.app_index

        print("Deployed new app with APP ID: "+str(TestContract.app_index))

        global_state = read_global_state(
                TestContract.algod_client, account.address_from_private_key(creator_private_key), TestContract.app_index
            )
        
        # assertions for state after app creation
        self.assertEqual(global_state['VoteBegin'], voteBegin)
        self.assertEqual(global_state['VoteEnd'], voteEnd)
        self.assertEqual(global_state['RegBegin'], regBegin)
        self.assertEqual(global_state['RegEnd'], regEnd)
        self.assertEqual(global_state['VotingToken'], voting_asa)

        #### TEST OPT-IN ####
        TestContract.app_index = opt_in_app(
            TestContract.algod_client,
            creator_private_key,
            TestContract.app_index,
        )

        #### TEST VOTE ####

        print(TestContract.app_index)

        vote_app_args = [
            bytes('voting', 'utf-8'),
            bytes('Yes', 'utf-8'),
        ]

        TestContract.app_index = call_app(
            TestContract.algod_client,
            creator_private_key,
            new_app_id,
            vote_app_args,
            [voting_asa],
        )


def tearDownClass(self) -> None:
    return super().tearDown()

if __name__ == '__main__':
    unittest.main()