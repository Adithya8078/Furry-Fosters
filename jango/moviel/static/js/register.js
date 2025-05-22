document.addEventListener("DOMContentLoaded", function() {
    const roleSelect = document.querySelector("#id_role");
    const licenseGroup = document.querySelector("#licenseNumberGroup");
    const fullNameLabel = document.querySelector("label[for='id_full_name']");
    
    // Show/hide license number and update full name label based on initial role value
    if (roleSelect.value === "foster") {
        fullNameLabel.textContent = "Foster Home Name";
        licenseGroup.style.display = "block";
    }

    roleSelect.addEventListener("change", function() {
        if (roleSelect.value === "foster") {
            fullNameLabel.textContent = "Foster Home Name"; // Update label text for full name
            licenseGroup.style.display = "block"; // Show license number input
        } else {
            fullNameLabel.textContent = "Full Name"; // Reset label text
            licenseGroup.style.display = "none"; // Hide license number input
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
const phoneInput = document.querySelector("input[name='phone_number']");
phoneInput.addEventListener("input", function (e) {
// Allow only digits in the input field
this.value = this.value.replace(/\D/g, '');
});
});