document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');
    const searchForm = document.createElement('form');
    searchForm.action = '/search';
    searchForm.method = 'GET';
    searchInput.parentNode.insertBefore(searchForm, searchInput);
    searchForm.appendChild(searchInput);

    // Handle form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    });

    // Handle Enter key press
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        }
    });
}); 