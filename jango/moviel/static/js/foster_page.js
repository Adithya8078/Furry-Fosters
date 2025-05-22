$(document).ready(function () {
    const formContainer = $('#formContainer');
    const overlay = $('.overlay');

    // Show the form modal
    $('#addPetButton').click(function () {
        formContainer.show();
        overlay.show();
    });

    // Hide the form modal when clicking outside
    overlay.click(function () {
        formContainer.hide();
        overlay.hide();
    });

    // Handle form submission with AJAX for adding a pet
    $('#addPetForm').on('submit', function (e) {
        e.preventDefault(); // Prevent default form submission
        const formData = new FormData(this);

        $.ajax({
            url: "{% url 'add_pet' %}",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    alert('Pet added successfully!');
                    location.reload();
                } else {
                    alert('Failed to add pet. Please try again.');
                }
            },
            error: function () {
                alert('An error occurred. Please try again.');
            }
        });
    });

    // Handle approval/rejection of requests with AJAX (for other forms)
    $(document).on('submit', 'form', function (e) {
        // Skip handling if it's the #addPetForm to avoid duplicate handling
        if ($(this).is('#addPetForm')) return;

        e.preventDefault(); // Prevent default form submission

        const form = $(this);
        const actionUrl = form.attr('action');

        // Get the value of the clicked button
        const status = form.find('button[type="submit"]:focus').val();

        // Include the CSRF token
        const csrfToken = $("input[name='csrfmiddlewaretoken']").val();

        $.ajax({
            url: actionUrl,
            type: "POST",
            data: {
                status: status,  // Send the clicked button's status
                csrfmiddlewaretoken: csrfToken  // Include CSRF token
            },
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    location.reload();  // Reload to reflect changes
                } else {
                    alert('Failed: ' + response.message);
                }
            },
            error: function () {
                alert('An error occurred. Please try again.');
            }
        });
    });
});