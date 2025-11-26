/**
 * AI Recruiting Demo - Upload Form Logic
 * Story 2.1: Basic File Upload UI & Route
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('cvFile');
    const fileName = document.getElementById('fileName');
    const submitBtn = document.getElementById('submitBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const uploadArea = document.getElementById('uploadArea');

    // File selection handler
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Update file name display
            fileName.textContent = file.name;
            fileName.style.color = '#2d3748';
            
            // Enable submit button
            submitBtn.disabled = false;
            
            // Highlight upload area
            uploadArea.classList.add('file-selected');
            
            // Hide any previous errors
            hideError();
            
            console.log('File selected:', file.name, 'Size:', file.size, 'bytes');
        } else {
            resetForm();
        }
    });

    // Form submission handler
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        
        if (!file) {
            showError('Bitte wählen Sie eine PDF-Datei');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        loadingSpinner.style.display = 'block';
        uploadArea.style.opacity = '0.5';
        hideError();

        // Create FormData
        const formData = new FormData();
        formData.append('cv_file', file);

        // Submit via fetch API
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Upload successful:', data);
                // Story 10: Reload page to show results (they're in session)
                window.location.reload();
            } else {
                showError(data.error || 'Upload fehlgeschlagen');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            showError('Verbindungsfehler. Bitte versuchen Sie es erneut.');
        })
        .finally(() => {
            // Hide loading state
            loadingSpinner.style.display = 'none';
            uploadArea.style.opacity = '1';
            submitBtn.disabled = fileInput.files.length === 0;
        });
    });

    // Helper: Show error message
    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        uploadArea.classList.add('error');
    }

    // Helper: Hide error message
    function hideError() {
        errorMessage.style.display = 'none';
        uploadArea.classList.remove('error');
    }

    // Helper: Reset form to initial state
    function resetForm() {
        fileInput.value = '';
        fileName.textContent = 'Keine Datei ausgewählt';
        fileName.style.color = '#a0aec0';
        submitBtn.disabled = true;
        uploadArea.classList.remove('file-selected');
        hideError();
    }

    // Drag & Drop support (basic, Story 2.1)
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    });
});

