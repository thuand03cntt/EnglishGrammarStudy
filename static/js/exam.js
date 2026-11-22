/**
 * EnglishPractice - Exam Client Engine
 * Features:
 * - Real-time stop-watch timer (counts up elapsed seconds)
 * - 10 questions per page client-side pagination
 * - Preserves state across pages and restores from localStorage
 * - Interactive question palette with answered status
 * - Submission confirmation modal with answered count summary
 */

document.addEventListener('DOMContentLoaded', function () {
    const examForm = document.getElementById('examForm');
    if (!examForm) return;

    const attemptId = examForm.getAttribute('data-attempt-id');
    const totalQuestions = parseInt(examForm.getAttribute('data-total-questions'), 10) || 10;
    const questionsPerPage = 10;
    const totalPages = Math.ceil(totalQuestions / questionsPerPage);

    let currentPage = 1;
    let elapsedSeconds = 0;
    let timerInterval = null;

    // Cache DOM elements
    const timerDisplay = document.getElementById('timerDisplay');
    const durationInput = document.getElementById('durationInput');
    const paginationContainer = document.getElementById('paginationControls');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageIndicator = document.getElementById('pageIndicator');
    const answeredCountBadge = document.getElementById('answeredCountBadge');

    // 1. Storage key for temporary safety backup
    const storageKey = `exam_state_${attemptId}`;

    // 2. Timer Initialization
    function formatTime(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        const pad = (n) => (n < 10 ? '0' + n : n);
        if (hrs > 0) {
            return `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
        }
        return `${pad(mins)}:${pad(secs)}`;
    }

    // Restore timer if stored
    const savedStateStr = localStorage.getItem(storageKey);
    let savedAnswers = {};
    if (savedStateStr) {
        try {
            const parsed = JSON.parse(savedStateStr);
            if (parsed.elapsedSeconds) {
                elapsedSeconds = parsed.elapsedSeconds;
            }
            if (parsed.answers) {
                savedAnswers = parsed.answers;
            }
        } catch (e) {
            console.warn('Could not parse saved exam state', e);
        }
    }

    timerInterval = setInterval(() => {
        elapsedSeconds++;
        if (timerDisplay) {
            timerDisplay.textContent = formatTime(elapsedSeconds);
        }
        if (durationInput) {
            durationInput.value = elapsedSeconds;
        }

        // Save elapsed time every 5 seconds
        if (elapsedSeconds % 5 === 0) {
            saveCurrentState();
        }
    }, 1000);

    // 3. Restore and Handle Radio Button Choices
    const allRadioInputs = document.querySelectorAll('.question-radio');

    // Restore answers from savedAnswers if radio not already checked
    allRadioInputs.forEach((radio) => {
        const qName = radio.getAttribute('name');
        if (savedAnswers[qName] && savedAnswers[qName] === radio.value) {
            radio.checked = true;
        }

        radio.addEventListener('change', function () {
            handleOptionSelection(this);
            saveCurrentState();
            updatePaletteStatus();
        });
    });

    function handleOptionSelection(radio) {
        // Remove .selected class from siblings in same question
        const parentQuestionCard = radio.closest('.question-card');
        if (parentQuestionCard) {
            parentQuestionCard.querySelectorAll('.option-label').forEach((label) => {
                label.classList.remove('selected');
            });
        }
        const currentLabel = radio.closest('.option-label');
        if (currentLabel) {
            currentLabel.classList.add('selected');
        }
    }

    // Trigger initial label highlight for pre-checked options
    allRadioInputs.forEach((radio) => {
        if (radio.checked) {
            handleOptionSelection(radio);
        }
    });

    function saveCurrentState() {
        const answers = {};
        allRadioInputs.forEach((radio) => {
            if (radio.checked) {
                answers[radio.getAttribute('name')] = radio.value;
            }
        });
        const payload = {
            elapsedSeconds: elapsedSeconds,
            answers: answers,
            updatedAt: Date.now()
        };
        localStorage.setItem(storageKey, JSON.stringify(payload));
    }

    // 4. Pagination Display Logic (10 questions per page)
    const questionCards = document.querySelectorAll('.question-card');

    function renderPage(pageNumber) {
        if (pageNumber < 1) pageNumber = 1;
        if (pageNumber > totalPages) pageNumber = totalPages;
        currentPage = pageNumber;

        const startIndex = (currentPage - 1) * questionsPerPage;
        const endIndex = startIndex + questionsPerPage;

        questionCards.forEach((card, index) => {
            if (index >= startIndex && index < endIndex) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });

        // Update Prev / Next buttons state
        if (prevPageBtn) {
            prevPageBtn.disabled = currentPage === 1;
        }
        if (nextPageBtn) {
            nextPageBtn.disabled = currentPage === totalPages;
        }
        if (pageIndicator) {
            pageIndicator.textContent = `Trang ${currentPage} / ${totalPages}`;
        }

        // Highlight current active palette buttons
        document.querySelectorAll('.page-btn').forEach((btn) => {
            const p = parseInt(btn.getAttribute('data-page'), 10);
            if (p === currentPage) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Scroll smoothly to top of question area
        const container = document.getElementById('examQuestionsArea');
        if (container) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => renderPage(currentPage - 1));
    }
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => renderPage(currentPage + 1));
    }

    // Page number buttons in footer
    document.querySelectorAll('.page-btn').forEach((btn) => {
        btn.addEventListener('click', function () {
            const targetPage = parseInt(this.getAttribute('data-page'), 10);
            renderPage(targetPage);
        });
    });

    // 5. Question Palette interaction
    const paletteButtons = document.querySelectorAll('.palette-btn');

    paletteButtons.forEach((btn) => {
        btn.addEventListener('click', function () {
            const orderIndex = parseInt(this.getAttribute('data-order'), 10); // 1-based
            const targetPage = Math.ceil(orderIndex / questionsPerPage);
            renderPage(targetPage);

            // Scroll to the specific question
            const targetCard = document.getElementById(`question-card-${orderIndex}`);
            if (targetCard) {
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetCard.classList.add('border-primary');
                setTimeout(() => targetCard.classList.remove('border-primary'), 1500);
            }
        });
    });

    function updatePaletteStatus() {
        let answeredCount = 0;

        questionCards.forEach((card) => {
            const order = card.getAttribute('data-order');
            const hasChecked = card.querySelector('input[type="radio"]:checked');
            const paletteBtn = document.getElementById(`palette-btn-${order}`);

            if (hasChecked) {
                answeredCount++;
                if (paletteBtn) {
                    paletteBtn.classList.add('answered');
                }
            } else {
                if (paletteBtn) {
                    paletteBtn.classList.remove('answered');
                }
            }
        });

        if (answeredCountBadge) {
            answeredCountBadge.textContent = `${answeredCount} / ${totalQuestions}`;
        }

        // Update modal info
        const modalAnswered = document.getElementById('modalAnsweredCount');
        const modalUnanswered = document.getElementById('modalUnansweredCount');
        if (modalAnswered) modalAnswered.textContent = answeredCount;
        if (modalUnanswered) modalUnanswered.textContent = (totalQuestions - answeredCount);
    }

    // Initial render
    renderPage(1);
    updatePaletteStatus();

    // 6. Form Submission and Cleanup
    const submitBtn = document.getElementById('confirmSubmitExamBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            if (durationInput) {
                durationInput.value = elapsedSeconds;
            }
            // Clear backup state upon final submit
            localStorage.removeItem(storageKey);
            clearInterval(timerInterval);
            examForm.submit();
        });
    }
});
