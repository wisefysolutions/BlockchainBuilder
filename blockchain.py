"""
Blockchain Module

This module provides a robust blockchain implementation with core functionalities
including proof of work, transaction management, chain validation, and node 
management for consensus.

Designed to be extendable and integrable with web frameworks like Flask or FastAPI.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Union
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Blockchain:
    """
    Blockchain class implementing core blockchain functionalities.
    
    This class provides methods for creating and managing a blockchain,
    including block mining, transaction management, and chain validation.
    """
    
    def __init__(self, difficulty: int = 4):
        """
        Initialize a new Blockchain.
        
        Args:
            difficulty: Number of leading zeros required for proof of work
                       (default: 4)
        """
        # Initialize the chain with the genesis block
        self.chain = []
        # Pending transactions to be included in the next block
        self.current_transactions = []
        # Set of nodes in the network
        self.nodes = set()
        # Difficulty level for proof of work
        self.difficulty = difficulty
        
        # Create the genesis block
        logger.info("Creating genesis block")
        self.create_block(proof=1, previous_hash='0')
    
    def create_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict:
        """
        Create a new block and add it to the blockchain.
        
        Args:
            proof: The proof value from the proof of work algorithm
            previous_hash: Hash of the previous block (optional, will be calculated if not provided)
        
        Returns:
            The newly created block as a dictionary
        """
        # If previous_hash is not provided, use the hash of the last block
        if previous_hash is None and self.chain:
            previous_hash = self.hash(self.chain[-1])
        
        # Define the block structure
        block = {
            'index': len(self.chain) + 1,
            'timestamp': datetime.now().isoformat(),
            'transactions': self.current_transactions.copy(),
            'proof': proof,
            'previous_hash': previous_hash
        }
        
        # Reset the current list of transactions
        self.current_transactions = []
        
        # Add the block to the chain
        self.chain.append(block)
        logger.info(f"Created block #{block['index']} with {len(block['transactions'])} transactions")
        
        return block
    
    def add_transaction(self, sender: str, recipient: str, amount: Union[int, float], **kwargs) -> int:
        """
        Add a new transaction to the list of transactions.
        
        Args:
            sender: Address of the sender
            recipient: Address of the recipient
            amount: Amount being transferred
            **kwargs: Additional transaction data
        
        Returns:
            The index of the block that will contain this transaction
        """
        # Create the transaction structure
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            **kwargs  # Include any additional transaction data
        }
        
        # Add the transaction to the list
        self.current_transactions.append(transaction)
        logger.debug(f"Added transaction: {sender} -> {recipient}: {amount}")
        
        # Return the index of the block that will contain this transaction
        # (the next one to be mined)
        return self.last_block['index'] + 1
    
    @property
    def last_block(self) -> Dict:
        """
        Return the last block in the chain.
        
        Returns:
            The last block in the chain as a dictionary
        """
        return self.chain[-1]
    
    @staticmethod
    def hash(block: Dict) -> str:
        """
        Create a SHA-256 hash of a block.
        
        Args:
            block: Block to hash
        
        Returns:
            Hash of the block as a string
        """
        # Ensure the dictionary is ordered to get consistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, last_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading zeros
          where p is the previous proof and p' is the new proof
        
        Args:
            last_proof: Previous proof
        
        Returns:
            New proof value
        """
        proof = 0
        target = '0' * self.difficulty
        
        logger.debug(f"Starting proof of work with difficulty {self.difficulty}")
        start_time = time.time()
        
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        duration = time.time() - start_time
        logger.info(f"Found proof {proof} in {duration:.2f} seconds")
        
        return proof
    
    def valid_proof(self, last_proof: int, proof: int) -> bool:
        """
        Validate the proof: Does hash(last_proof, proof) start with leading zeros?
        
        Args:
            last_proof: Previous proof
            proof: Current proof
        
        Returns:
            True if correct, False if not
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == '0' * self.difficulty
    
    def is_valid_chain(self, chain: List[Dict]) -> bool:
        """
        Determine if a given blockchain is valid.
        
        Args:
            chain: A blockchain
            
        Returns:
            True if valid, False if not
        """
        if not chain:
            logger.error("Empty chain provided, invalid")
            return False
            
        # Check if the chain has a valid genesis block
        if (chain[0]['previous_hash'] != '0' or
            chain[0]['proof'] != 1):
            logger.error("Invalid genesis block")
            return False
        
        # Check the integrity of the chain
        for i in range(1, len(chain)):
            block = chain[i]
            prev_block = chain[i - 1]
            
            # Check that the hash of the previous block is correct
            if block['previous_hash'] != self.hash(prev_block):
                logger.error(f"Invalid hash at block {i}")
                return False
                
            # Check that the Proof of Work is correct
            if not self.valid_proof(prev_block['proof'], block['proof']):
                logger.error(f"Invalid proof at block {i}")
                return False
                
        logger.info("Chain validated successfully")
        return True
    
    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes.
        
        Args:
            address: URL of the node to add (e.g., 'http://192.168.0.5:5000')
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accept an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')
        
        logger.info(f"Registered node: {address}")
    
    def resolve_conflicts(self) -> bool:
        """
        Consensus Algorithm: Resolve conflicts by replacing our chain with
        the longest valid chain in the network.
        
        Returns:
            True if our chain was replaced, False if not
        """
        neighbors = self.nodes
        new_chain = None
        
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        
        # Grab and verify the chains from all nodes in our network
        for node in neighbors:
            try:
                # Make a request to get the node's chain
                response = requests.get(f'http://{node}/chain')
                
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    
                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.is_valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.RequestException as e:
                logger.error(f"Error connecting to node {node}: {e}")
        
        # Replace our chain if we found a longer valid one
        if new_chain:
            self.chain = new_chain
            logger.info(f"Chain replaced with a longer one of length {max_length}")
            return True
            
        logger.info("Our chain is authoritative")
        return False
    
    def mine_block(self) -> Dict:
        """
        Mine a new block by running the proof of work algorithm.
        
        Returns:
            The newly mined block
        """
        # Get the last block's proof
        last_block = self.last_block
        last_proof = last_block['proof']
        
        # Run the proof of work algorithm to get the next proof
        proof = self.proof_of_work(last_proof)
        
        # Create a new block and add it to the chain
        previous_hash = self.hash(last_block)
        block = self.create_block(proof, previous_hash)
        
        return block
