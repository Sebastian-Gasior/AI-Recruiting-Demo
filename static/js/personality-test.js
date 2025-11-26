/**
 * AI Recruiting Demo - Personality Test (Big Five IPIP-30)
 * Story 11.3: UI Fragebogen
 */

let questions = [];
let currentQuestionIndex = 0;
let answers = {}; // {questionId: answerValue}
let testStarted = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Personality Test JS loaded');
    
    // Check if test already started in session
    checkTestStatus();
    
    // Start button handler
    const startBtn = document.getElementById('startPersonalityTest');
    if (startBtn) {
        startBtn.addEventListener('click', startPersonalityTest);
    }
    
    // Navigation buttons
    const btnBack = document.getElementById('btnBack');
    const btnNext = document.getElementById('btnNext');
    
    if (btnBack) {
        btnBack.addEventListener('click', goToPreviousQuestion);
    }
    
    if (btnNext) {
        btnNext.addEventListener('click', goToNextQuestion);
    }
});

/**
 * Check if test was already started (from session)
 */
async function checkTestStatus() {
    try {
        const response = await fetch('/api/personality/status');
        if (response.ok) {
            const data = await response.json();
            if (data.started && data.current_question_index >= 0) {
                // Test was already started, restore state
                testStarted = true;
                currentQuestionIndex = data.current_question_index || 0;
                answers = data.answers || {};
                await loadQuestions();
                showQuestionScreen();
                displayQuestion(currentQuestionIndex);
            }
        }
    } catch (error) {
        console.log('No existing test session found');
    }
}

/**
 * Load questions from backend
 */
async function loadQuestions() {
    try {
        const response = await fetch('/api/personality/questions');
        if (!response.ok) {
            throw new Error('Failed to load questions');
        }
        
        const data = await response.json();
        questions = data.questions || [];
        
        console.log(`Loaded ${questions.length} questions`);
        return questions;
    } catch (error) {
        console.error('Error loading questions:', error);
        showError('Fehler beim Laden der Fragen. Bitte Seite neu laden.');
        return [];
    }
}

/**
 * Start the personality test
 */
async function startPersonalityTest() {
    console.log('Starting personality test...');
    
    // Hide intro screen
    const introScreen = document.getElementById('personalityIntro');
    if (introScreen) {
        introScreen.style.display = 'none';
    }
    
    // Load questions
    await loadQuestions();
    
    if (questions.length === 0) {
        showError('Keine Fragen gefunden. Bitte Seite neu laden.');
        return;
    }
    
    // Reset state
    testStarted = true;
    currentQuestionIndex = 0;
    answers = {};
    
    // Initialize session on backend
    try {
        await fetch('/api/personality/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    } catch (error) {
        console.error('Error starting test session:', error);
    }
    
    // Show question screen
    showQuestionScreen();
    displayQuestion(0);
}

/**
 * Show question screen
 */
function showQuestionScreen() {
    const questionContainer = document.getElementById('personalityQuestionContainer');
    if (questionContainer) {
        questionContainer.style.display = 'block';
    }
}

/**
 * Display current question
 */
function displayQuestion(index) {
    if (index < 0 || index >= questions.length) {
        console.error(`Invalid question index: ${index}`);
        return;
    }
    
    const question = questions[index];
    currentQuestionIndex = index;
    
    // Update progress
    updateProgress(index + 1, questions.length);
    
    // Update question number
    const questionNumberEl = document.getElementById('questionNumber');
    if (questionNumberEl) {
        questionNumberEl.textContent = `Frage ${index + 1}`;
    }
    
    // Update question text
    const questionTextEl = document.getElementById('questionText');
    if (questionTextEl) {
        questionTextEl.textContent = `"${question.text}"`;
    }
    
    // Generate Likert scale
    generateLikertScale(question.id, answers[question.id]);
    
    // Update navigation buttons
    updateNavigationButtons();
}

/**
 * Generate Likert scale radio buttons
 */
function generateLikertScale(questionId, selectedValue) {
    const likertScale = document.getElementById('likertScale');
    if (!likertScale) return;
    
    const options = [
        { value: 1, label: 'Trifft überhaupt nicht zu' },
        { value: 2, label: 'Trifft eher nicht zu' },
        { value: 3, label: 'Weder noch' },
        { value: 4, label: 'Trifft eher zu' },
        { value: 5, label: 'Trifft völlig zu' }
    ];
    
    likertScale.innerHTML = '';
    
    options.forEach(option => {
        const label = document.createElement('label');
        label.className = 'likert-option';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = `q${questionId}`;
        radio.value = option.value;
        radio.id = `q${questionId}_${option.value}`;
        
        // Check if this option was previously selected
        if (selectedValue && parseInt(selectedValue) === option.value) {
            radio.checked = true;
        }
        
        // Store answer when changed
        radio.addEventListener('change', function() {
            answers[questionId] = parseInt(option.value);
            updateNavigationButtons();
            saveProgress();
        });
        
        const span = document.createElement('span');
        span.textContent = option.label;
        
        label.appendChild(radio);
        label.appendChild(span);
        
        likertScale.appendChild(label);
    });
}

/**
 * Update progress bar
 */
function updateProgress(current, total) {
    const percentage = (current / total) * 100;
    
    const progressBar = document.getElementById('questionProgressBar');
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
    
    const progressText = document.getElementById('questionProgressText');
    if (progressText) {
        progressText.textContent = `Frage ${current}/${total}`;
    }
}

/**
 * Update navigation buttons state
 */
function updateNavigationButtons() {
    const btnBack = document.getElementById('btnBack');
    const btnNext = document.getElementById('btnNext');
    
    // Back button
    if (btnBack) {
        btnBack.disabled = currentQuestionIndex === 0;
    }
    
    // Next button - disabled if current question not answered
    if (btnNext) {
        const currentQuestion = questions[currentQuestionIndex];
        const isAnswered = answers[currentQuestion.id] !== undefined;
        btnNext.disabled = !isAnswered;
        
        // Change text on last question
        if (currentQuestionIndex === questions.length - 1) {
            btnNext.textContent = 'Abschließen →';
        } else {
            btnNext.textContent = 'Weiter →';
        }
    }
}

/**
 * Go to previous question
 */
function goToPreviousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion(currentQuestionIndex);
    }
}

/**
 * Go to next question or submit
 */
function goToNextQuestion() {
    // Save current answer
    saveProgress();
    
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        displayQuestion(currentQuestionIndex);
    } else {
        // Last question - submit
        submitTest();
    }
}

/**
 * Save progress to backend
 */
async function saveProgress() {
    try {
        await fetch('/api/personality/progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answers: answers,
                current_question_index: currentQuestionIndex
            })
        });
    } catch (error) {
        console.error('Error saving progress:', error);
    }
}

/**
 * Submit test and show results
 */
async function submitTest() {
    // Check if all questions answered
    const unanswered = questions.filter(q => !answers[q.id]);
    if (unanswered.length > 0) {
        const confirmMsg = `${unanswered.length} Fragen sind noch unbeantwortet. Möchten Sie den Test trotzdem abschließen?`;
        if (!confirm(confirmMsg)) {
            return;
        }
    }
    
    // Disable submit button
    const btnNext = document.getElementById('btnNext');
    if (btnNext) {
        btnNext.disabled = true;
        btnNext.textContent = 'Wird verarbeitet...';
    }
    
    // Debug: Log answers before sending
    console.log('Submitting test with answers:', answers);
    console.log('Number of answered questions:', Object.keys(answers).length);
    
    try {
        const response = await fetch('/api/personality/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answers: answers
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit test');
        }
        
        const data = await response.json();
        
        // Hide question screen
        const questionContainer = document.getElementById('personalityQuestionContainer');
        if (questionContainer) {
            questionContainer.style.display = 'none';
        }
        
        // Show results
        showResults(data);
        
    } catch (error) {
        console.error('Error submitting test:', error);
        showError('Fehler beim Absenden des Tests. Bitte versuchen Sie es erneut.');
        
        // Re-enable submit button
        if (btnNext) {
            btnNext.disabled = false;
            btnNext.textContent = 'Abschließen →';
        }
    }
}

/**
 * Show results screen
 */
function showResults(data) {
    const resultsContainer = document.getElementById('personalityResultsContainer');
    const scoresDisplay = document.getElementById('oceanScoresDisplay');
    
    if (!resultsContainer || !scoresDisplay) return;
    
    // Display OCEAN scores
    const dimensions = ['O', 'C', 'E', 'A', 'N'];
    const dimensionNames = {
        'O': 'Openness (Offenheit)',
        'C': 'Conscientiousness (Gewissenhaftigkeit)',
        'E': 'Extraversion',
        'A': 'Agreeableness (Verträglichkeit)',
        'N': 'Neuroticism (Neurotizismus)'
    };
    
    scoresDisplay.innerHTML = '';
    
    dimensions.forEach(dim => {
        const score = data.scores[dim];
        const percentage = ((score - 6) / 24) * 100; // 6-30 range to percentage
        const level = data.interpretations[dim].level;
        const description = data.interpretations[dim].description;
        
        const scoreCard = document.createElement('div');
        scoreCard.className = 'ocean-score-card';
        
        scoreCard.innerHTML = `
            <div class="score-header">
                <h3>${dimensionNames[dim]}</h3>
                <span class="score-value">${score}/30</span>
            </div>
            <div class="progress-bar-large">
                <div class="progress-fill" style="width: ${percentage}%;"></div>
            </div>
            <p class="score-interpretation">
                <strong>${level}</strong> - ${description}
            </p>
        `;
        
        scoresDisplay.appendChild(scoreCard);
    });
    
    // Display Personality Fit Score if available
    if (data.fit_score !== undefined) {
        const fitScore = data.fit_score;
        const fitInterpretation = data.fit_interpretation || {};
        const fitLevel = fitInterpretation.level || '';
        const fitDescription = fitInterpretation.description || '';
        
        const fitCard = document.createElement('div');
        fitCard.className = 'personality-fit-card';
        
        // Determine color based on score
        let fitColor = '#667eea'; // Default
        if (fitScore >= 80) {
            fitColor = '#48bb78'; // Green
        } else if (fitScore >= 65) {
            fitColor = '#667eea'; // Blue
        } else if (fitScore >= 50) {
            fitColor = '#ed8936'; // Orange
        } else {
            fitColor = '#fc8181'; // Red
        }
        
        fitCard.innerHTML = `
            <h3>Personality Fit Score</h3>
            <div class="fit-score-circle" style="border-color: ${fitColor};">
                <div class="fit-score-value" style="color: ${fitColor};">
                    ${fitScore}/100
                </div>
                <div class="fit-score-level">${fitLevel}</div>
            </div>
            <p class="fit-description">${fitDescription}</p>
        `;
        
        scoresDisplay.appendChild(fitCard);
    }
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Scroll to top
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Show error message
 */
function showError(message) {
    alert(message); // TODO: Replace with better error display
}

