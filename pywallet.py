import json
from web3 import Web3
from eth_account import Account
from bip_utils import Bip39SeedGenerator, Bip44Coins, Bip44, Bip44Changes, Bip39EntropyBitLen, Bip39EntropyGenerator, Bip39MnemonicGenerator, Bip39WordsNum, Bip39Languages
import ast
import time


class pywallet:
    def connect(self, node='infura', network='mainnet', connection='HTTP'):
        """
        Node: geth, infura
        Network: mainnet, ropsten, rinkeby...
        Connection: ipc, websocket, http
        """
        self.node = node.lower()
        self.network = network.lower()
        self.connection = connection.lower()
        if connection == 'ipc':
            if self.node == 'infura':
                raise ValueError(
                    'Infure not available with connection type IPC')
            else:
                if self.network == 'mainnet':
                    self.web3 = Web3(Web3.IPCProvider('~/.ethereum/geth.ipc'))
                else:
                    self.web3 = Web3(Web3.IPCProvider(
                        '~/.ethereum/geth' + network + '/geth.ipc'))

        elif self.connection == 'websocket':
            if self.node == 'infura':
                with open('/mnt/c/blockchain/api_keys/infura.json') as f:
                    self.infdata = json.load(f)
                self.infurl = "wss://" + network + ".infura.io/ws/v3/" + \
                    self.infdata['web3_eth1']['project_id']
                self.web3 = Web3(Web3.WebsocketProvider(self.infurl))
            else:
                raise ValueError('Geth websocket not yet implemented')

        elif self.connection == 'http':
            if self.node == 'infura':
                with open('/mnt/c/blockchain/api_keys/infura.json') as f:
                    self.infdata = json.load(f)
                self.infurl = "https://" + network + ".infura.io/v3/" + \
                    self.infdata['web3_eth1']['project_id']
                self.web3 = Web3(Web3.HTTPProvider(self.infurl))
            else:
                raise ValueError('Geth HTTP not yet implemented')
        else:
            raise ValueError('Invalid connection type')

        return self.web3

    # This contains unaudited web3py account generation code, feel free to use this rather
    # than the dedicated address generation packages if you feel safer only using web3py
    ##########################################################################################
    # def create_account(self, use_mnemonic:bool=True, extra_entropy:str=None, passphrase:str='', num_words:int=12, language:str='english', derivation_path:str="m/44'/60'/0'/0/0") -> tuple or LocalAccount:
    #     """
    #     extra_entropy (optional): Only required if use_mnemonic == False, should be randomly generated string
    #     num_words: [12, 15, 18, 21, 24]
    #     language: 'english', 'spanish', etc...
    #     derivation_path: defaults to using BIP44 compliant m/44'/60'/0'/0/0

    #     Using mnemonic is currently an unaudited feature which
    #     is advised to be likely to change, please use at your
    #     own risk.  Returns a tuple of LocalAccount object and
    #     mnemonic phrases if use_mnemonic == True, else only a
    #     LocalAccount object is returned.
    #     """

    #     if use_mnemonic:

    #         Account.enable_unaudited_hdwallet_features()
    #         self.acct = Account.create_with_mnemonic(
    #                                                     passphrase=passphrase,
    #                                                     num_words=num_words,
    #                                                     language=language,
    #                                                     account_path=derivation_path)
    #         return self.acct

    #     else:

    #         # if not extra_entropy:
    #         #     raise ValueError('Please provide extra_entropy')

    #         self.acct = Account.create(extra_entropy=extra_entropy)

    #         return self.acct

#####################################################################
#####################################################################
# Add more coins?

    def create_account(self, num_words: int = 12, language='english'):
        """
        num_words: [12, 15, 18, 21, 24]
        language: ['chinese (simplified)', 'chinese (tradional', 
                    'czech', 'english', 'french', 'italian', 
                    'korean', 'portuguese', 'spanish']
        """
        self.num_words_dict = {
            12: Bip39WordsNum.WORDS_NUM_12,
            15: Bip39WordsNum.WORDS_NUM_15,
            18: Bip39WordsNum.WORDS_NUM_18,
            21: Bip39WordsNum.WORDS_NUM_21,
            24: Bip39WordsNum.WORDS_NUM_24
        }

        self.language_dict = {
            'chinese (simplified)': Bip39Languages.CHINESE_SIMPLIFIED,
            'chinese (tradional': Bip39Languages.CHINESE_TRADITIONAL,
            'czech': Bip39Languages.CZECH,
            'english': Bip39Languages.ENGLISH,
            'french': Bip39Languages.FRENCH,
            'italian': Bip39Languages.ITALIAN,
            'korean': Bip39Languages.KOREAN,
            'portuguese': Bip39Languages.PORTUGUESE,
            'spanish': Bip39Languages.SPANISH
        }

        self.mnemonic = Bip39MnemonicGenerator(
            self.language_dict[language]).FromWordsNumber(self.num_words_dict[num_words])
        self.seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()
        bip44_def_ctx = Bip44.FromSeed(
            self.seed_bytes, Bip44Coins.ETHEREUM).DeriveDefaultPath()

        self.account_details = {
            'address': bip44_def_ctx.PublicKey().ToAddress(),
            'private_key': bip44_def_ctx.PrivateKey().Raw().ToHex(),
            'public_key': bip44_def_ctx.PublicKey().RawCompressed().ToHex(),
            'mnemonic': self.mnemonic.ToStr()
        }

        return self.account_details

    def encrypt_and_save(self, private_key, password: str, filepath: str, kdf: str = None, iterations: int = None):
        """
        private_key: (hex str, bytes, int or eth_keys.datatypes.PrivateKey)
        filepath: Absolute path including filename and extension, saves as json
        kdf: The key derivation function to use when encrypting your private key, scrypt is default
        iterations: The work factor for the key derivation function, must be a power of 2 and < 2**32
        """
        self.encrypted = Account.encrypt(
            private_key, password, kdf, iterations)

        with open(filepath, 'w') as f:
            f.write(json.dumps(self.encrypted))

        print('File saved successfully')

    def decrypt(self, keyfile_json: dict or str, password: str) -> dict:
        """
        Decrypts keyfile and returns in json format
        """
        self.decrypted = Account.decrypt(keyfile_json, password)

        return self.decrypted

    def get_balance(self, token, public_address, contract_address_json, ABI, currency_for_quote='ether'):
        """
        Get the balance of a particular token
        """
        if not Web3.isAddress(public_address):
            raise ValueError(
                'The public address is not recognized as a valid format')
        else:
            if token == 'ETH':
                self.wei = web3.eth.getBalance(public_address)
                self.balance = float(web3.fromWei(
                    self.wei, currency_for_quote))

            else:
                self.cpubkey = Web3.toChecksumAddress(public_address)

                try:
                    self.contract_address_json = contract_address_json[token]
                except Exception:
                    raise ValueError(
                        'Specified coin not in contract_address json, please add it and try again')
                self.ccontract_address = Web3.toChecksumAddress(
                    self.contract_address_json)
                self.contract = web3.eth.contract(
                    self.ccontract_address, abi=ABI)
                self.balance = self.contract.functions.balanceOf(
                    self.cpubkey).call()

            return self.balance

    # Gas Fee Estimation

    def gas_limiter(self, transaction_speed='average', custom_maxpriorityfee=None, basefeemultiple=2):
        """
        Estimates priority fee and gets current base fee
        to determine a reasonable maxFeePerGas for the
        transaction.  Allows for a user specified
        transaction_speed, which applied to the
        maxpriorityfee to either increase/decrease
        the tip to miners, speeding/slowing the
        time to process the transaction.

        transaction_speed: 'very_slow', 'slow', 'average', 'fast', 'custom_multiple'

        very_slow = .5
        slow = .75
        average = 1
        fast = 1.25

        maxpriorityfee_est * transaction_speed = maxpriorityfee

        If a custom_priorityfee is specified it will override
        the default maxpriorityfee with the specified amount.
        Must be entered in Wei.

        maxfeepergas can be increased/decreased by specifying
        by specifiying a custom basefeemultiple, default is 2.
        This is since maxfeepergas = (basefeemultiple * currentbasefee)
        + maxpriorityfeepergas
        """
        # Pulls an estimate of current priority fees (miner fees) using Geth's calculation (look online for current info on how this is done)
        if custom_maxpriorityfee:
            self.maxpriorityfee = custom_maxpriorityfee
        else:
            if not isinstance(transaction_speed, str):
                self.multiple = transaction_speed
            else:
                self.transaction_speed = transaction_speed.lower()
                self.multiple_dict = {'very_slow': .5,
                                      'slow': .75, 'average': 1, 'fast': 1.25}
                if transaction_speed in self.multiple_dict:
                    self.multiple = self.multiple_dict[transaction_speed]
                else:
                    raise ValueError(
                        'transaction_speed specified is not a recognized value')

            # Pulls the current base fee from the next block after the pending one, the next block's base fee is predermined by the pending block and is therefore certain
            self.maxpriorityfee_est = web3.eth.max_priority_fee
            self.maxpriorityfee = int(self.maxpriorityfee_est * self.multiple)

        self.currentbasefee = web3.toWei(web3.eth.fee_history(1, 'pending')[
                                         'baseFeePerGas'][-1], 'gwei')
        # This is the seemingly universally agreed upon formula for the maxFeePerGas (basefeemultiple defaults to 2, increase to raise maxfeepergas)
        self.maxfeepergas = (
            basefeemultiple * self.currentbasefee) + self.maxpriorityfee
        return (self.maxfeepergas, self.maxpriorityfee)

    # Creating and sending transaction

    def send_transaction(self, from_address, from_private_key, to_address, value, gas_tuple, token, contract_address=None, ABI=erc20_ABI, network='mainnet', gas_multiple=1):
        """
        Creates and sends a transaction.
        gas_tuple should be in format:
            (maxFeePerGas, maxPriorityFeePerGas)

        """
        if network in chain_ids:
            chainId = chain_ids[network]
        else:
            raise ValueError(
                'Invalid network or network not in chain_ids.json')
        self.tx = {
            'nonce': web3.eth.get_transaction_count(from_address),
            'to': to_address,
            'value': value,
            'gas': int(web3.eth.estimate_gas({'to': to_address, 'from': from_address, 'value': value}) * gas_multiple),
            'maxFeePerGas': int(gas_tuple[0]),
            'maxPriorityFeePerGas': int(gas_tuple[1]),
            'chainId': chainId
        }
        if token.lower() != 'eth':
            contract = web3.eth.contract(
                address=contract_address[token], abi=ABI)
            del self.tx['to']
            del self.tx['value']
            self.tx = contract.functions.transfer(
                to_address, value).buildTransaction(self.tx)

        self.signed_tx = web3.eth.account.signTransaction(
            self.tx, from_private_key)
        self.tx_hash = web3.eth.sendRawTransaction(
            self.signed_tx.rawTransaction)
        return self.tx_hash
