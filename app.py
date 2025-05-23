"""
Blockchain API Application

This module provides a Flask web application that exposes the blockchain
functionality through a RESTful API and a web interface for visualization.
"""

import os
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for
from blockchain import Blockchain

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "blockchain-secret-key")

# Generate a unique node identifier
node_identifier = os.environ.get("NODE_ID", "node1")

# Create an instance of the Blockchain
blockchain = Blockchain(difficulty=4)

@app.route('/')
def index():
    """Render the blockchain explorer interface."""
    return render_template('index.html', 
                          chain=blockchain.chain, 
                          transactions=blockchain.current_transactions,
                          node_id=node_identifier,
                          node_count=len(blockchain.nodes),
                          blockchain=blockchain)

@app.route('/mine', methods=['GET', 'POST'])
def mine():
    """
    Mine a new block.
    
    Returns:
        JSON response with the new block information
    """
    # Mine a new block
    block = blockchain.mine_block()
    
    response = {
        'message': 'New block mined',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    
    if request.method == 'POST':
        return jsonify(response), 201
    else:
        # Redirect to home page after mining via GET request
        return redirect(url_for('index'))

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Create a new transaction.
    
    Returns:
        JSON response with the transaction status
    """
    values = request.get_json()
    
    # Check that the required fields are in the POST data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return jsonify({'message': 'Missing values'}), 400
    
    # Create a new transaction
    index = blockchain.add_transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount']
    )
    
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    """
    Return the full blockchain.
    
    Returns:
        JSON response with the complete chain and its length
    """
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register new nodes in the network.
    
    Returns:
        JSON response with registration status
    """
    values = request.get_json()
    
    nodes = values.get('nodes')
    if nodes is None:
        return jsonify({'message': 'Error: Please supply a valid list of nodes'}), 400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET', 'POST'])
def consensus():
    """
    Resolve conflicts using the consensus algorithm.
    
    Returns:
        JSON response with the consensus result
    """
    replaced = blockchain.resolve_conflicts()
    
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    
    if request.method == 'POST':
        return jsonify(response), 200
    else:
        # Redirect to home page after consensus via GET request
        return redirect(url_for('index'))

@app.route('/validate', methods=['GET', 'POST'])
def validate_chain():
    """
    Validate the current blockchain.
    
    Returns:
        JSON response with the validation result
    """
    is_valid = blockchain.is_valid_chain(blockchain.chain)
    
    response = {
        'valid': is_valid,
        'chain': blockchain.chain
    }
    
    if request.method == 'POST':
        return jsonify(response), 200
    else:
        # Redirect to home page after validation via GET request
        return redirect(url_for('index'))

@app.route('/transaction', methods=['POST'])
def create_transaction_web():
    """
    Create a new transaction from the web form.
    
    Returns:
        Redirect to the home page
    """
    sender = request.form.get('sender')
    recipient = request.form.get('recipient')
    amount = request.form.get('amount')
    
    if sender and recipient and amount:
        try:
            amount = float(amount)
            blockchain.add_transaction(sender, recipient, amount)
        except ValueError:
            logger.error(f"Invalid amount: {amount}")
    
    return redirect(url_for('index'))

@app.route('/node', methods=['POST'])
def register_node_web():
    """
    Register a new node from the web form.
    
    Returns:
        Redirect to the home page
    """
    node = request.form.get('node')
    
    if node:
        try:
            blockchain.register_node(node)
        except ValueError as e:
            logger.error(f"Invalid node address: {e}")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
