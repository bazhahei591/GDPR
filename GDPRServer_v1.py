# -*- coding: utf-8 -*-
import hashlib
import json
from textwrap import dedent
from datetime import datetime
import time
from uuid import uuid4

from flask import Flask
from flask import jsonify
from flask import request


class Blockchain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        生成新块
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        timestamp = int(time.time())
        block = {
            "index": len(self.chain) + 1,
            "timestamp": timestamp,            
            "transactions": self.current_transactions,
            "proof": proof,
            # "self_hash":self.hash(self.chain),
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        } 

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    # def new_transaction_user(self, type, userId, commonId, boolean, datetime):
    def new_transaction_user(self, type, userId, commonId, boolean,timestamp):
    
        # Adds a new transaction to the list of user permission record.
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param type: <int> 0 for user, 1 for company
        :param userId: <str> User id for each user
        :param commonId: <str> Foreign key from transaction_cpny
        :param boolean: <boolean> Agree with the permission as 1 or disagree as 0
        :param timestamp: <time> Time of this transaction happen (utc)
        :return: <int> The index of the Block that will hold this transaction
        """
        timestamp = int(time.time())
        self.current_transactions.append(
            {
                "type": 0,
                "userId": userId,
                "commonId": commonId,
                "boolean": 0,
                "timestamp": timestamp,
            }
        )

        return self.last_block["index"] + 1

    def new_transaction_cpny(self, type, commonId, version, cpnyId, timestamp, text):
        # Adds a new transaction to the list of company permission record.
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param type: <int> 0 for user, 1 for company
        :param commonId: <str> Permission id to show the same permission (with different version)
        :param version: <int> Permission version 
        :param cpnyId: <str> Company id for each company
        :param timestamp: <int> Time of this transaction happen (utc)
        :param text: <str> Text of each permission
        """
        timestamp = int(time.time())
        self.current_transactions.append(
            {
                "type": 1,
                "commonId": commonId,
                "version": version,
                "cpnyId": cpnyId,
                "time": timestamp,
                "text":text
            }
        )

        return self.last_block["index"] + 1

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明:
         - 查找一个 p' 使得 hash(pp') 以4个0开头
         - p 是上一个块的证明,  p' 是当前的证明
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        # guess = f'{last_proof}{proof}'.encode()
        guess =('%s%s'%(last_proof, proof)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        生成块的 SHA-256 hash值
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace("-", "")

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route("/userPermission",methods=["POST"])
def userModify():
    
    #return "We will modify state of a permission"
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required=["type","userId","commonId","boolean","timestamp"]
    # required=["type","userId","commonId","boolean"]    
    if not all(k in values for k in required):
        return "Missing values", 400
    
    # Create a new Transaction
    index = blockchain.new_transaction_user(
        values["type"],values["userId"],values["commonId"],values["boolean"],values["timestamp"]
    )

    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    block = blockchain.new_block(proof)

    response = {'message':"Thank You and add to Block %s" % (index)}
    return jsonify(response),201

@app.route("/cpnyPermission",methods=["POST"])
def cpnyModify():
    #return "we will modify a permission"
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required=["type","commonId","version","cpnyId","timestamp","text"]
    if not all(k in values for k in required):
        return "Missing values", 400
    
    # Create a new Transaction
    index = blockchain.new_transaction_cpny(
        values["type"],values["commonId"],values["version"],values["cpnyId"],values["timestamp"],values["text"]
        # values["type"],values["commonId"],values["version"],values["cpnyId"]
    )

    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    block = blockchain.new_block(proof)

    response = {'message':"Thank You and modify added  to Block %s" % (index)}
    return jsonify(response),201

@app.route("/cpnyCheck",methods=["POST"])
def cpnyCheck():
    # return "We will check the state of permission"
    '''
    Determine if a given permission of specific user's state
    :return: <bool> True if the user agree, False if not
    '''
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required=["userId","commonId","timestamp"]

    if not all(k in values for k in required):
        return "Missing values", 400

    # last_block = blockchain.chain[0]
    current_index = 1

    while current_index < len(blockchain.chain):
        block = blockchain.chain[current_index]
        tranTmp = block["transactions"]
        transacTmp = tranTmp[0]
        
        # if (block["type"]==0 and block["userId"]==values["userId"] and block["commonId"]== values["commonId"]):
        if (transacTmp["type"]== 0): 
            if transacTmp["userId"]==values["userId"]: 
                if transacTmp["commonId"]== values["commonId"]:
        
                    state = transacTmp["boolean"]
                    break
        else:
            current_index += 1
    
    response = {'Permission':state, 'PermissionTime':transacTmp["timestamp"]}
    return jsonify(response),201

@app.route("/chain", methods=["GET"])
def full_chain():
    response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(response), 200


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0",port=5001)