document.addEventListener('DOMContentLoaded', function() {
    // Add to Cart functionality
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const formData = new FormData();
            formData.append('quantity', 1);

            fetch(`/cart/add/${productId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Update cart count if it exists
                    const cartCountElements = document.querySelectorAll('.cart-count');
                    cartCountElements.forEach(element => {
                        element.textContent = data.cart_count;
                    });
                } else {
                    showToast(data.message || 'Failed to add to cart', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Failed to add to cart. Please try again.', 'error');
            });
        });
    });

    // Wishlist functionality
    document.querySelectorAll('.toggle-wishlist-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const isInWishlist = this.dataset.inWishlist === 'true';
            const wishlistItemId = this.dataset.wishlistItemId;
            const icon = this.querySelector('svg');
            const isWishlistPage = document.getElementById('wishlist-grid') !== null;
            
            if (isInWishlist) {
                // Remove from wishlist
                fetch(`/wishlist/remove/${wishlistItemId}`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (isWishlistPage) {
                            // Find the wishlist item container and animate its removal
                            const wishlistItem = document.querySelector(`.wishlist-item[data-product-id="${productId}"]`);
                            if (wishlistItem) {
                                wishlistItem.style.transition = 'all 0.3s ease-out';
                                wishlistItem.style.opacity = '0';
                                wishlistItem.style.transform = 'scale(0.9)';
                                
                                setTimeout(() => {
                                    wishlistItem.remove();
                                    
                                    // Check if wishlist is empty and show empty state
                                    const remainingItems = document.querySelectorAll('.wishlist-item');
                                    if (remainingItems.length === 0) {
                                        const wishlistGrid = document.getElementById('wishlist-grid');
                                        wishlistGrid.innerHTML = `
                                            <div class="bg-white shadow-sm rounded-lg p-8 text-center col-span-full">
                                                <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                                </svg>
                                                <h3 class="mt-4 text-lg font-medium text-gray-900">Your wishlist is empty</h3>
                                                <p class="mt-2 text-gray-500">Browse our products and add items to your wishlist</p>
                                                <div class="mt-6">
                                                    <a href="/products" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500">
                                                        Browse Products
                                                    </a>
                                                </div>
                                            </div>
                                        `;
                                    }
                                }, 300);
                            }
                        } else {
                            // Update button state for non-wishlist pages
                            this.dataset.inWishlist = 'false';
                            this.classList.remove('text-red-500', 'hover:text-red-600');
                            this.classList.add('text-gray-400', 'hover:text-red-500');
                            icon.setAttribute('fill', 'none');
                            delete this.dataset.wishlistItemId;
                        }
                        showToast('Removed from wishlist', 'success');
                    } else {
                        showToast(data.message || 'Failed to remove from wishlist', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Failed to remove from wishlist', 'error');
                });
            } else {
                // Add to wishlist
                fetch(`/wishlist/add/${productId}`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.dataset.inWishlist = 'true';
                        this.dataset.wishlistItemId = data.wishlist_item_id;
                        this.classList.remove('text-gray-400', 'hover:text-red-500');
                        this.classList.add('text-red-500', 'hover:text-red-600');
                        icon.setAttribute('fill', 'currentColor');
                        showToast('Added to wishlist', 'success');
                    } else {
                        showToast(data.message || 'Failed to add to wishlist', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Failed to add to wishlist', 'error');
                });
            }
        });
    });

    // Helper function to show toast messages
    function showToast(message, type = 'success') {
        // Remove any existing toasts
        const existingToasts = document.querySelectorAll('.toast-message');
        existingToasts.forEach(toast => toast.remove());

        // Create new toast
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in-up toast-message ${
            type === 'success' ? 'bg-emerald-500' : 'bg-red-500'
        } text-white`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.style.transition = 'all 0.3s ease-out';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}); 