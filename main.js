document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // File input validation & UI feedback
    const fileInput = document.getElementById('resume');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileNameDisplay = document.querySelector('.custom-file-feedback');
            const validFileTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/json'];
            
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileName = file.name;
                const fileType = file.type;
                
                // Check if file type is allowed
                if (validFileTypes.includes(fileType) || 
                    (fileType === '' && (fileName.endsWith('.pdf') || fileName.endsWith('.docx') || fileName.endsWith('.json')))) {
                    this.setCustomValidity('');
                } else {
                    this.setCustomValidity('Please select a PDF, DOCX, or JSON file.');
                }
            }
        });
    }

    // Experience list toggle details
    const expItems = document.querySelectorAll('.experience-list .list-group-item');
    if (expItems) {
        expItems.forEach(item => {
            item.addEventListener('click', function() {
                const details = this.querySelector('.experience-details');
                if (details) {
                    if (details.style.display === '-webkit-box' || details.style.display === '') {
                        details.style.display = 'block';
                        details.style.webkitLineClamp = 'unset';
                    } else {
                        details.style.display = '-webkit-box';
                        details.style.webkitLineClamp = '3';
                    }
                }
            });
        });
    }
});
