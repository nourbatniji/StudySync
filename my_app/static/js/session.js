document.addEventListener('DOMContentLoaded', () => {
    create_form = document.getElementById('CreateSession')
    create_form.addEventListener('submit', function (e) {
        e.preventDefault()
        const formdata = new FormData(create_form)
        fetch('/add_session/', {
            method: 'POST',
            body: formdata
        })
            .then(res => res.json())
            .then(data => {
                if (data.success == false) {
                    if (data.errors.title) {
                        document.getElementById('title_valid').innerHTML += data.errors.title
                    }
                    if (data.errors.meet_link) {
                        document.getElementById('url_valid').innerHTML += data.errors.meet_link
                    }
                    if (data.errors.not_unique) {
                        document.getElementById('url_not_unique').innerHTML += data.errors.not_unique
                    }
                    if (data.errors.date) {
                        document.getElementById('date_valid').innerHTML += data.errors.date
                    }
                }
                else {
                    create_form.reset()
                    const modalElement = create_form.closest('.modal');  // find the parent modal of this form
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    modal.hide();
                    window.location.reload();
                }
            })
    })

    update_forms = document.querySelectorAll('#UpdateSession')
    update_forms.forEach(update_form => {
        update_form.addEventListener('submit', function (e) {
            e.preventDefault()
            const formdata = new FormData(update_form)

            fetch('/update_session/', {
                method: 'POST',
                body: formdata
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success == false) {
                        console.log(data);

                        if (data.update_errors.title) {
                            document.querySelectorAll('.edit_title_valid').forEach(error => {
                                error.innerHTML += data.update_errors.title
                            });
                        }
                        if (data.update_errors.meet_link) {
                            document.querySelectorAll('.edit_url_valid').forEach(error => {
                                error.innerHTML += data.update_errors.meet_link
                            });
                        }
                        if (data.update_errors.not_unique) {
                            document.querySelectorAll('.edit_url_not_unique').forEach(error => {
                                error.innerHTML += data.update_errors.not_unique
                            });
                        }
                        if (data.update_errors.date) {
                            document.querySelectorAll('.edit_date_valid').forEach(error => {
                                error.innerHTML += data.update_errors.date
                            });
                        }
                    }
                    else {
                        update_form.reset()
                        const modalElement = update_form.closest('.modal');  // find the parent modal of this form
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        modal.hide();
                        window.location.reload();
                    }
                })
        })
    });

    // Handle attend button clicks
    const attendForms = document.querySelectorAll('#attend-form');
    attendForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const button = form.querySelector('.btn-attend');
            const formData = new FormData(form);
            
            // Disable button to prevent double-clicks
            button.disabled = true;
            button.textContent = 'Processing...';
            
            fetch('/attend_session', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Update button to show attended state
                    button.textContent = 'Attended ✓';
                    button.classList.remove('btn-attend');
                    button.classList.add('btn-attended');
                    
                    // Update attendee count
                    const sessionId = formData.get('session_id');
                    const countElement = document.querySelector(`#count-${sessionId} #count`);
                    if (countElement) {
                        countElement.textContent = data.attendee_count;
                    }
                } else {
                    // Show error message
                    alert(data.message || 'Failed to register for session');
                    button.disabled = false;
                    button.textContent = 'Attend';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                button.disabled = false;
                button.textContent = 'Attend';
            });
        });
    });
})