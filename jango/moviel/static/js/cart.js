function filterCart(button) {
    const filterValue = button.getAttribute('data-filter');
    const items = document.querySelectorAll('.cart-item');
    const buttons = document.querySelectorAll('.filter-btn');

    // Update active button styling
    buttons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');

    // Filter items
    items.forEach(item => {
        const itemStatus = item.getAttribute('data-status');
        if (filterValue === 'all' || filterValue === itemStatus) {
            item.style.display = 'flex'; // Show matching items
        } else {
            item.style.display = 'none'; // Hide non-matching items
        }
    });
}