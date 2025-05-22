document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    const petGrid = document.querySelector('.pet-grid');
    const viewAllLink = document.querySelector('.view-all');
    const searchLoading = document.querySelector('.search-loading');

    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = searchInput.value;
        
        // Update the view all link with the search query
        viewAllLink.href = `/pets/?query=${query}`;
        
        // Show loading indicator
        searchLoading.classList.remove('hidden');

        fetch(`/home/?query=${query}`, {  // Changed URL to /home/
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            petGrid.innerHTML = data.html;
            // Add fade-in animation to new results
            const cards = petGrid.querySelectorAll('.pet-card');
            cards.forEach(card => {
                card.style.opacity = '0';
                card.style.animation = 'fadeInUp 0.5s ease-out forwards';
            });
            // Hide loading indicator
            searchLoading.classList.add('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            searchLoading.classList.add('hidden');
        });
    });

    // Add live search functionality
    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        
        // Show loading indicator
        searchLoading.classList.remove('hidden');
        
        debounceTimer = setTimeout(() => {
            const query = this.value;
            
            // Update the view all link
            viewAllLink.href = `/pets/?query=${query}`;

            fetch(`/home/?query=${query}`, {  // Changed URL to /home/
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                petGrid.innerHTML = data.html;
                // Add fade-in animation to new results
                const cards = petGrid.querySelectorAll('.pet-card');
                cards.forEach(card => {
                    card.style.opacity = '0';
                    card.style.animation = 'fadeInUp 0.5s ease-out forwards';
                });
                // Hide loading indicator
                searchLoading.classList.add('hidden');
            })
            .catch(error => {
                console.error('Error:', error);
                searchLoading.classList.add('hidden');
            });
        }, 300);
    });
});