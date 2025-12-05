let timer;
let minutes = 1;
let seconds = 0;
let isPaused = false;
let enteredTime = null;

// default duration for first run
let originalDuration = 1;

function startTimer() {
    clearInterval(timer);
    isPaused = false;
    timer = setInterval(updateTimer, 1000);
}

function updateTimer() {
    const timerElement = document.getElementById('timer');
    timerElement.textContent = formatTime(minutes, seconds);

    if (minutes === 0 && seconds === 0) {
        clearInterval(timer);

        // 1) save minutes to DB via AJAX
        saveMinutes(originalDuration);
        timeFinished();

        return;
    }

    if (!isPaused) {
        if (seconds > 0) {
            seconds--;
        } else {
            seconds = 59;
            minutes--;
        }
    }
}

function formatTime(minutes, seconds) {
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function togglePauseResume() {
    const pauseResumeButton = document.querySelector('.control-buttons button');
    isPaused = !isPaused;

    if (isPaused) {
        clearInterval(timer);
        pauseResumeButton.textContent = 'Resume';
    } else {
        startTimer();
        pauseResumeButton.textContent = 'Pause';
    }
}

function restartTimer() {
    clearInterval(timer);
    minutes = enteredTime || originalDuration;
    seconds = 0;
    isPaused = false;

    const timerElement = document.getElementById('timer');
    timerElement.textContent = formatTime(minutes, seconds);

    const pauseResumeButton = document.querySelector('.control-buttons button');
    pauseResumeButton.textContent = 'Pause';

    startTimer();
}

function chooseTime() {
    const newTime = document.getElementById('chosen-time');
    enteredTime = parseInt(newTime.value, 10);
    minutes = enteredTime;
    originalDuration = enteredTime;
    seconds = 0;

    clearInterval(timer);
    isPaused = true;

    const timerElement = document.getElementById('timer');
    timerElement.textContent = formatTime(minutes, seconds);
}

function timeFinished() {
    const modalEl = document.getElementById('finishModal');
    if (!modalEl) return;

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}


function saveMinutes(minutesToAdd) {
    console.log("Saving minutes:", minutesToAdd);

    // Update the UI total immediately
    const minutesEl = document.getElementById('minutes-studied');
    const currentTotal = parseInt(minutesEl.textContent) || 0;
    const newTotal = currentTotal + minutesToAdd;
    minutesEl.textContent = newTotal;

    // Prepare POST data
    const csrfInput = document.querySelector('#pomodoroForm input[name="csrfmiddlewaretoken"]');
    if (!csrfInput) {
        console.error("CSRF token not found");
        return;
    }
    const csrfToken = csrfInput.value;

    const formData = new URLSearchParams();
    formData.append('minutes', minutesToAdd);

    fetch('/pomodoroForm', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
    })
        .then(res => {
            if (!res.ok) {
                console.error("Error saving minutes:", res.status);
            }
            // we ignore redirect, page stays as is
        })
        .catch(err => console.error("Fetch error:", err));
}
document.addEventListener('DOMContentLoaded', () => {
    // get tasks belong to the chosen exam
    document.getElementById("exam_id").addEventListener("change", function () {
        let examId = this.value;

        fetch(`/get_tasks/${examId}/`)
            .then(response => response.json())
            .then(data => {
                let taskSelect = document.getElementById("task_id");
                let no_option = document.getElementById("no-option");
                if (data.length === 0) {
                    no_option.innerHTML = `No Tasks To Do`;
                    return;  //do not continue
                }
                let startTimer = document.getElementById("startTimer");
                taskSelect.innerHTML = ""; // clear old tasks
                startTimer.disabled = false

                data.forEach(task => {
                    taskSelect.innerHTML += `<option value="${task.id}">${task.title}</option>`;
                });
            });

    });

    //to display the currently studying exam and task
    document.getElementById("task_id").addEventListener("change", function () {
        let taskId = this.value; //chosen taskid
        console.log(taskId);

        fetch(`get_exam_task/${taskId}/`) //chosen task
            .then(response => response.json())
            .then(data => {
                const current_subject = document.getElementById("current-subject");
                const current_task = document.getElementById("current-task");
                const hiddenInput = document.getElementById("finished_task_id");

                current_subject.innerHTML = "";
                current_task.innerHTML = "";
                hiddenInput.value = taskId;


                data.forEach(data => {
                    box = document.getElementById('current-box')
                    box.style.display = 'block'

                    current_subject.innerHTML += data.exam_id__title
                    current_task.innerHTML += data.title
                });
            })
    })
})
