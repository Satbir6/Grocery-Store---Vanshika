document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.getAttribute('data-product-id');
            const isInWishlist = this.getAttribute('data-in-wishlist') === 'true';
            const wishlistItemId = this.getAttribute('data-wishlist-item-id');
            
            if (isInWishlist) {
                removeFromWishlist(wishlistItemId, this);
            } else {
                addToWishlist(productId, this);
            }
        });
    });
    
    // Function to add a product to wishlist
    function addToWishlist(productId, button) {
        fetch(`/wishlist/add/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update button state
                button.setAttribute('data-in-wishlist', 'true');
                button.setAttribute('data-wishlist-item-id', data.wishlist_item_id);
                
                // Update button appearance
                button.classList.remove('text-gray-400', 'hover:text-red-500');
                button.classList.add('text-red-500', 'hover:text-red-600');
                
                // Show success message if needed
                showToast(data.message || 'Added to wishlist!');
            } else {
                showToast(data.message || 'Error adding to wishlist');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error adding to wishlist');
        });
    }
    
    // Function to remove a product from wishlist
    function removeFromWishlist(wishlistItemId, button) {
        fetch(`/wishlist/remove/${wishlistItemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update button state
                button.setAttribute('data-in-wishlist', 'false');
                button.removeAttribute('data-wishlist-item-id');
                
                // Update button appearance
                button.classList.remove('text-red-500', 'hover:text-red-600');
                button.classList.add('text-gray-400', 'hover:text-red-500');
                
                // Show success message if needed
                showToast(data.message || 'Removed from wishlist!');
            } else {
                showToast(data.message || 'Error removing from wishlist');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error removing from wishlist');
        });
    }
    
    // Simple toast notification function
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-opacity duration-300';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Fade in
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}); 