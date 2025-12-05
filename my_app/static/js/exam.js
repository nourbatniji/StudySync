document.addEventListener('DOMContentLoaded', () => {
    exam = document.getElementById('CreateExam')

    exam.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(exam)

        fetch(`/add_exam/`, {
            method: "POST",
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                if (data.success == false) {
                    if (data.errors.exam_name) {
                        document.getElementById('title_valid').innerHTML += data.errors.exam_name
                    }
                    if (data.errors.exam_date) {
                        document.getElementById('date_valid').innerHTML += data.errors.exam_date
                    }
                }
                else {
                    exam.reset()
                    const modal = bootstrap.Modal.getInstance(document.getElementById('postExamModal'))
                    modal.hide()
                    window.location.reload();
                }
            })

    })

    updateExamForms = document.querySelectorAll('#UpdateExam')
    updateExamForms.forEach(updateExamForm => {
        updateExamForm.addEventListener('submit', function (e) {
            e.preventDefault()
            const update_form = new FormData(updateExamForm)

            fetch(`/update_exam/`, {
                method: 'POST',
                body: update_form
            })

                .then(res => res.json())
                .then(data => {
                    if (data.success == false) {
                        if (data.errors.exam_name) {
                            document.querySelectorAll('.edit_title_valid').forEach(input => {
                                input.innerHTML += data.errors.exam_name
                            });
                        }
                        if (data.errors.exam_date) {
                            document.querySelectorAll('.edit_date_valid').forEach(input => {
                                input.innerHTML += data.errors.exam_date
                            });
                        }
                    }
                    else {
                        updateExamForm.reset()
                        const modalElement = updateExamForm.closest('.modal');  // find the parent modal of this form
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        modal.hide();
                        window.location.reload();
                    }
                })
        })
    })


    const tasks = document.querySelectorAll('.task-check');

    tasks.forEach(task => {
        task.addEventListener('change', function (e) {
            e.preventDefault();

            const checkTaskForm = task.closest('form');
            const formData = new FormData(checkTaskForm);

            fetch(`/check_task/`, {
                method: 'POST',
                body: formData
            })
                .then(res => res.json())
                .then(data => {
                    // find the exam container of this task
                    const examBox = checkTaskForm.closest('.border');
                    const completedSpan = examBox.querySelector('.completed-count');

                    completedSpan.textContent = data.data;   // only this exam is updated
                });
        });
    });
})