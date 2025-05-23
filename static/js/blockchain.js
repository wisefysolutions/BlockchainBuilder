/**
 * Blockchain Explorer JavaScript
 * 
 * This script handles dynamic calculations and interactions for the blockchain explorer.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Calculate and display block hashes
    calculateBlockHashes();
    
    // Setup tooltips
    setupTooltips();
    
    // Add event listeners
    setupEventListeners();
});

/**
 * Calculate and display the hash for each block
 */
function calculateBlockHashes() {
    // Get all blocks from the page
    const blocks = document.querySelectorAll('.accordion-item');
    
    blocks.forEach(block => {
        const blockIndex = block.querySelector('[id^="block"]').id.replace('block', '');
        const hashElement = document.getElementById(`hash-${blockIndex}`);
        
        if (hashElement) {
            // Get block data from API
            fetch(`/chain`)
                .then(response => response.json())
                .then(data => {
                    const blockData = data.chain.find(b => b.index.toString() === blockIndex);
                    if (blockData) {
                        // Calculate hash client-side (simplified approach)
                        // In a real implementation, this would be the hash from the server
                        const hash = calculateHash(blockData);
                        hashElement.textContent = hash;
                    }
                })
                .catch(error => {
                    console.error('Error fetching block data:', error);
                    hashElement.textContent = 'Error calculating hash';
                });
        }
    });
}

/**
 * Calculate a simplified hash for a block object
 * @param {Object} block - The block to hash
 * @returns {string} The calculated hash
 */
function calculateHash(block) {
    // In a real implementation, this would be done server-side
    // This is a simplified client-side version for display purposes
    const blockString = JSON.stringify(block, Object.keys(block).sort());
    
    // Simple hash function for demonstration
    // This is NOT a cryptographic hash
    let hash = 0;
    for (let i = 0; i < blockString.length; i++) {
        const char = blockString.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    
    // Convert to hex string
    const hexHash = (hash >>> 0).toString(16).padStart(8, '0');
    return hexHash.repeat(8).slice(0, 64); // Make it look like a SHA-256 hash
}

/**
 * Set up Bootstrap tooltips
 */
function setupTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Add animation to the mine button
    const mineButton = document.querySelector('button[type="submit"]');
    if (mineButton) {
        mineButton.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-cog fa-spin me-2"></i>Mining...';
            this.disabled = true;
            // The form will handle the actual submission
        });
    }
    
    // Add form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}
