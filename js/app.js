/**
 * app.js
 * Main application coordinator for LIS CBT Examination Website.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // DOM View Containers
  const viewWelcome = document.getElementById('view-welcome');
  const viewExam = document.getElementById('view-exam');
  const viewResult = document.getElementById('view-result');
  const viewReview = document.getElementById('view-review');

  // Anti-Tab Switching & Proctoring Security State
  let tabSwitchCount = 0;
  const MAX_TAB_SWITCHES = 3;
  const modalTabWarning = document.getElementById('modal-tab-warning');
  const tabViolationCountEl = document.getElementById('tab-violation-count');
  const btnTabWarningAck = document.getElementById('btn-tab-warning-ack');
  const btnFullscreen = document.getElementById('btn-fullscreen');

  // Welcome View Elements
  const btnStartExam = document.getElementById('btn-start-exam');
  const chkDeclaration = document.getElementById('chk-declaration');
  const bannerResume = document.getElementById('banner-resume');
  const btnResumeSession = document.getElementById('btn-resume-session');
  const btnDiscardSession = document.getElementById('btn-discard-session');
  const verifiedBankCountEl = document.getElementById('verified-bank-count');

  // Exam View Elements
  const timerDisplay = document.getElementById('timer-display');
  const timerBadge = document.getElementById('timer-badge');
  const qnoBadge = document.getElementById('qno-badge');
  const qnoDisplay = document.getElementById('qno-display');
  const promptEnEl = document.getElementById('prompt-en');
  const promptHiEl = document.getElementById('prompt-hi');
  const optionsContainer = document.getElementById('options-container');
  const selectLang = document.getElementById('select-lang');
  const sourceRefBadge = document.getElementById('source-ref-badge');

  // Exam Actions
  const btnPrev = document.getElementById('btn-prev');
  const btnClear = document.getElementById('btn-clear');
  const btnReviewNext = document.getElementById('btn-review-next');
  const btnSaveNext = document.getElementById('btn-save-next');
  const btnSubmitExam = document.getElementById('btn-submit-exam');
  const btnTogglePalette = document.getElementById('btn-toggle-palette');
  const paletteSidebar = document.getElementById('palette-sidebar');

  // Palette Elements
  const paletteGrid = document.getElementById('palette-grid');
  const countAnswered = document.getElementById('count-answered');
  const countNotAnswered = document.getElementById('count-not-answered');
  const countNotVisited = document.getElementById('count-not-visited');
  const countMarked = document.getElementById('count-marked');
  const countAnsweredMarked = document.getElementById('count-answered-marked');

  // Modal Confirmation Elements
  const modalConfirm = document.getElementById('modal-confirm-submit');
  const modalTotal = document.getElementById('modal-total');
  const modalAnswered = document.getElementById('modal-answered');
  const modalNotAnswered = document.getElementById('modal-not-answered');
  const modalMarked = document.getElementById('modal-marked');
  const modalAnsweredMarked = document.getElementById('modal-answered-marked');
  const modalNotVisited = document.getElementById('modal-not-visited');
  const btnModalCancel = document.getElementById('btn-modal-cancel');
  const btnModalConfirm = document.getElementById('btn-modal-confirm');

  // Core App State
  const engine = new ExamEngine();
  let timerInstance = null;
  let activeLanguage = 'both'; // 'both', 'en', 'hi'

  // --- Initial Setup & Data Loading ---
  try {
    const bank = await QuestionBank.loadQuestions();
    if (verifiedBankCountEl) {
      verifiedBankCountEl.textContent = bank.length;
    }
  } catch (e) {
    console.error('Failed to initialize question bank:', e);
    if (verifiedBankCountEl) {
      verifiedBankCountEl.textContent = '470';
    }
  }

  // Check for existing active session or completed result
  checkExistingSession();

  // --- View Switcher ---
  function showView(viewName) {
    viewWelcome.classList.add('hidden');
    viewExam.classList.add('hidden');
    viewResult.classList.add('hidden');
    viewReview.classList.add('hidden');

    if (viewName === 'welcome') viewWelcome.classList.remove('hidden');
    else if (viewName === 'exam') viewExam.classList.remove('hidden');
    else if (viewName === 'result') viewResult.classList.remove('hidden');
    else if (viewName === 'review') viewReview.classList.remove('hidden');

    window.scrollTo(0, 0);
  }

  function checkExistingSession() {
    const existing = Storage.getSession();
    const lastResult = Storage.getLastResult();

    if (existing && !existing.submitted && existing.questions && existing.questions.length > 0) {
      const remainingMs = existing.deadline - Date.now();
      if (remainingMs > 0) {
        if (bannerResume) {
          bannerResume.classList.remove('hidden');
          const minsLeft = Math.ceil(remainingMs / 60000);
          bannerResume.querySelector('.resume-text').textContent = 
            `You have an active in-progress exam attempt with ${minsLeft} minutes remaining.`;
        }
        return;
      } else {
        // Expired in background -> auto submit and clear
        engine.resumeExam(existing);
        const result = engine.submitExam(true);
        showResultsView(result);
        return;
      }
    }

    if (lastResult && !existing) {
      // User can view their last score card from welcome view
      const prevResultBox = document.getElementById('prev-result-box');
      if (prevResultBox) {
        prevResultBox.classList.remove('hidden');
        document.getElementById('prev-score-val').textContent = lastResult.finalScore;
        document.getElementById('prev-accuracy-val').textContent = lastResult.accuracy + '%';
        document.getElementById('btn-view-prev-result').addEventListener('click', () => {
          showResultsView(lastResult);
        });
      }
    }
  }

  // --- Start Exam Flow ---
  if (chkDeclaration) {
    chkDeclaration.addEventListener('change', () => {
      btnStartExam.disabled = !chkDeclaration.checked;
    });
  }

  btnStartExam.addEventListener('click', () => {
    // Start fresh 100-question randomized attempt
    const count = Math.min(100, QuestionBank.getVerifiedCount());
    engine.startNewExam(count);
    startExamView();
  });

  if (btnResumeSession) {
    btnResumeSession.addEventListener('click', () => {
      const existing = Storage.getSession();
      if (existing) {
        engine.resumeExam(existing);
        startExamView(true);
      }
    });
  }

  if (btnDiscardSession) {
    btnDiscardSession.addEventListener('click', () => {
      if (confirm('Are you sure you want to discard your previous attempt and start a fresh exam?')) {
        Storage.clearSession();
        if (bannerResume) bannerResume.classList.add('hidden');
      }
    });
  }

  function startExamView(isResumed = false) {
    showView('exam');
    tabSwitchCount = 0;

    // Request fullscreen for distraction-free / secure CBT exam environment
    try {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    } catch (e) {}

    // Setup timer
    if (timerInstance) timerInstance.stop();
    timerInstance = new ExamTimer(
      engine.deadline,
      (formatted, secondsLeft, urgency) => {
        timerDisplay.textContent = formatted;
        timerBadge.className = `timer-badge timer-${urgency}`;
      },
      () => {
        // Timeout callback
        alert('Time is up! Your examination will now be automatically submitted.');
        handleExamSubmission(true);
      }
    );
    timerInstance.start();

    // Hook state changes
    engine.onStateChange = () => {
      renderActiveQuestion();
      renderPalette();
    };

    renderActiveQuestion();
    renderPalette();
  }

  // --- Render Question in Exam View ---
  function renderActiveQuestion() {
    const qData = engine.getCurrentQuestion();
    if (!qData) return;

    qnoBadge.textContent = `Question ${qData.questionNumber}`;
    qnoDisplay.textContent = `Question ${qData.questionNumber} of ${qData.totalQuestions}`;

    // Language view filtering & cleanup of pseudo-Hindi OCR noise
    let enText = qData.data.question_en || qData.data.question;
    let hiText = qData.data.question_hi || '';

    // Check if Hindi text contains genuine Devanagari Unicode characters
    const hasRealHindi = /[\u0900-\u097F]/.test(hiText);

    // If English text contains multiple question marks or trailing Latin noise, trim to first '?'
    if (enText.includes('?') && enText.lastIndexOf('?') !== enText.indexOf('?')) {
      const qIdx = enText.indexOf('?');
      enText = enText.substring(0, qIdx + 1).trim();
    }
    // Clean any stray trailing slash or bracket
    enText = enText.replace(/[\/\(\[\{]+$/, '').trim();

    promptEnEl.textContent = enText;
    promptHiEl.textContent = hiText;

    if (activeLanguage === 'en') {
      promptEnEl.classList.remove('hidden');
      promptHiEl.classList.add('hidden');
    } else if (activeLanguage === 'hi') {
      if (hasRealHindi) {
        promptEnEl.classList.add('hidden');
        promptHiEl.classList.remove('hidden');
      } else {
        promptEnEl.classList.remove('hidden');
        promptHiEl.classList.add('hidden');
      }
    } else {
      // Both (Bilingual): only display Hindi panel if genuine Devanagari is present
      promptEnEl.classList.remove('hidden');
      if (hasRealHindi) {
        promptHiEl.classList.remove('hidden');
      } else {
        promptHiEl.classList.add('hidden');
      }
    }

    if (sourceRefBadge) {
      sourceRefBadge.textContent = `${qData.data.source_file} (Page ${qData.data.source_page}, Q#${qData.data.original_question_number})`;
    }

    // Previous button state
    btnPrev.disabled = qData.index === 0;

    // Render answer options
    optionsContainer.innerHTML = '';
    for (const opt of qData.shuffledOptions) {
      const isChecked = qData.selectedOption === opt.id;
      const optionRow = document.createElement('label');
      optionRow.className = `option-row ${isChecked ? 'selected' : ''}`;
      optionRow.setAttribute('for', `opt-${opt.id}`);

      optionRow.innerHTML = `
        <input type="radio" name="cbt_answer" id="opt-${opt.id}" value="${opt.id}" ${isChecked ? 'checked' : ''} />
        <span class="option-letter">(${opt.id})</span>
        <span class="option-text">${escapeHtml(opt.text)}</span>
      `;

      optionRow.addEventListener('click', () => {
        // Highlight row
        document.querySelectorAll('.option-row').forEach(r => r.classList.remove('selected'));
        optionRow.classList.add('selected');
        const input = optionRow.querySelector('input');
        input.checked = true;
      });

      optionsContainer.appendChild(optionRow);
    }
  }

  // --- Render Question Palette ---
  function renderPalette() {
    paletteGrid.innerHTML = '';
    const counts = engine.getSummaryCounts();

    countAnswered.textContent = counts.answered;
    countNotAnswered.textContent = counts.notAnswered;
    countNotVisited.textContent = counts.notVisited;
    countMarked.textContent = counts.marked;
    countAnsweredMarked.textContent = counts.answeredMarked;

    for (let i = 0; i < engine.questions.length; i++) {
      const btn = document.createElement('button');
      const status = engine.getQuestionStatus(i);
      const isCurrent = i === engine.currentIndex;

      btn.className = `palette-btn status-${status} ${isCurrent ? 'current-q' : ''}`;
      btn.textContent = i + 1;
      btn.setAttribute('aria-label', `Question ${i + 1}: ${getStatusLabel(status)}`);
      btn.title = `Question ${i + 1} (${getStatusLabel(status)})`;

      btn.addEventListener('click', () => {
        // Preserve selected option before jumping if user clicked an option
        const currentSelected = getSelectedRadioValue();
        if (currentSelected) {
          engine.userAnswers[engine.currentIndex] = currentSelected;
        }
        engine.navigateTo(i);
      });

      paletteGrid.appendChild(btn);
    }
  }

  function getStatusLabel(status) {
    switch (status) {
      case 'answered': return 'Answered';
      case 'not-answered': return 'Not Answered';
      case 'marked': return 'Marked for Review';
      case 'answered-marked': return 'Answered & Marked for Review';
      default: return 'Not Visited';
    }
  }

  function getSelectedRadioValue() {
    const checked = document.querySelector('input[name="cbt_answer"]:checked');
    return checked ? checked.value : null;
  }

  // --- Button Action Handlers ---
  btnSaveNext.addEventListener('click', () => {
    const selected = getSelectedRadioValue();
    engine.saveAndNext(selected);
  });

  btnReviewNext.addEventListener('click', () => {
    const selected = getSelectedRadioValue();
    engine.markForReviewAndNext(selected);
  });

  btnClear.addEventListener('click', () => {
    engine.clearResponse();
    // Uncheck in DOM
    const checked = document.querySelector('input[name="cbt_answer"]:checked');
    if (checked) checked.checked = false;
    document.querySelectorAll('.option-row').forEach(r => r.classList.remove('selected'));
  });

  btnPrev.addEventListener('click', () => {
    const selected = getSelectedRadioValue();
    if (selected) {
      engine.userAnswers[engine.currentIndex] = selected;
    }
    if (engine.currentIndex > 0) {
      engine.navigateTo(engine.currentIndex - 1);
    }
  });

  if (selectLang) {
    selectLang.addEventListener('change', (e) => {
      activeLanguage = e.target.value;
      renderActiveQuestion();
    });
  }

  // Mobile Palette Toggle
  if (btnTogglePalette && paletteSidebar) {
    btnTogglePalette.addEventListener('click', () => {
      paletteSidebar.classList.toggle('open');
    });
  }

  // Keyboard Shortcuts for examination efficiency
  document.addEventListener('keydown', (e) => {
    if (viewExam.classList.contains('hidden')) return;
    if (modalConfirm && !modalConfirm.classList.contains('hidden')) return;

    if (e.key === 'ArrowRight') {
      btnSaveNext.click();
    } else if (e.key === 'ArrowLeft' && !btnPrev.disabled) {
      btnPrev.click();
    }
  });

  // --- Submission & Confirmation Flow ---
  btnSubmitExam.addEventListener('click', () => {
    // Preserve current selection before showing modal
    const selected = getSelectedRadioValue();
    if (selected) {
      engine.userAnswers[engine.currentIndex] = selected;
    }

    const counts = engine.getSummaryCounts();
    modalTotal.textContent = counts.total;
    modalAnswered.textContent = counts.answered;
    modalNotAnswered.textContent = counts.notAnswered;
    modalMarked.textContent = counts.marked;
    modalAnsweredMarked.textContent = counts.answeredMarked;
    modalNotVisited.textContent = counts.notVisited;

    modalConfirm.classList.remove('hidden');
  });

  btnModalCancel.addEventListener('click', () => {
    modalConfirm.classList.add('hidden');
  });

  btnModalConfirm.addEventListener('click', () => {
    modalConfirm.classList.add('hidden');
    handleExamSubmission(false);
  });

  function handleExamSubmission(isAutoSubmit = false) {
    if (timerInstance) timerInstance.stop();
    const result = engine.submitExam(isAutoSubmit);
    showResultsView(result);
  }

  // --- Results View Flow ---
  function showResultsView(result) {
    showView('result');
    const container = document.getElementById('result-content-container');
    ResultsDashboard.render(result, container);

    document.getElementById('btn-review-answers').addEventListener('click', () => {
      showReviewView(result);
    });

    document.getElementById('btn-retake-exam').addEventListener('click', () => {
      triggerRetake();
    });

    document.getElementById('btn-result-home').addEventListener('click', () => {
      showView('welcome');
      checkExistingSession();
    });
  }

  // --- Review View Flow ---
  function showReviewView(result) {
    showView('review');
    const container = document.getElementById('review-content-container');
    AnswerReview.render(result, container);

    document.getElementById('btn-back-to-dashboard').addEventListener('click', () => {
      showResultsView(result);
    });

    document.getElementById('btn-review-retake').addEventListener('click', () => {
      triggerRetake();
    });
  }

  function triggerRetake() {
    if (confirm('Start a new attempt? This will generate a fresh randomized selection of 100 questions from the verified question bank.')) {
      Storage.clearSession();
      const count = Math.min(100, QuestionBank.getVerifiedCount());
      engine.startNewExam(count);
      startExamView();
    }
  }

  // --- Anti-Tab Switching / Anti-Cheating Proctoring Engine ---
  function handleTabSwitchViolation() {
    // Only monitor when candidate is actively inside the exam view and not submitted
    if (viewExam.classList.contains('hidden')) return;
    if (engine.submitted) return;

    tabSwitchCount++;
    if (tabViolationCountEl) {
      tabViolationCountEl.textContent = tabSwitchCount;
    }

    if (tabSwitchCount >= MAX_TAB_SWITCHES) {
      if (modalTabWarning) modalTabWarning.classList.add('hidden');
      alert(`SECURITY VIOLATION: Maximum allowed tab switches (${MAX_TAB_SWITCHES}) exceeded!\nYour examination has been terminated and submitted automatically.`);
      handleExamSubmission(true);
    } else {
      if (modalTabWarning) {
        modalTabWarning.classList.remove('hidden');
      }
    }
  }

  // 1. Detect visibility change (switching tabs or minimizing window)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      handleTabSwitchViolation();
    }
  });

  // 2. Detect window blur (losing focus, clicking desktop or other applications)
  window.addEventListener('blur', () => {
    handleTabSwitchViolation();
  });

  // 3. Acknowledge warning and resume exam
  if (btnTabWarningAck) {
    btnTabWarningAck.addEventListener('click', () => {
      if (modalTabWarning) modalTabWarning.classList.add('hidden');
      // Re-enter fullscreen mode
      try {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        }
      } catch (err) {}
    });
  }

  // 4. Fullscreen Toggle Button in Header
  if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch((err) => {
          console.warn('Fullscreen request denied:', err);
        });
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });

    document.addEventListener('fullscreenchange', () => {
      const fsText = btnFullscreen.querySelector('.fs-text');
      if (fsText) {
        fsText.textContent = document.fullscreenElement ? 'Exit Fullscreen' : 'Fullscreen';
      }
    });
  }

  // 5. Prevent leaving active exam (beforeunload confirmation)
  window.addEventListener('beforeunload', (e) => {
    if (!viewExam.classList.contains('hidden') && !engine.submitted) {
      e.preventDefault();
      e.returnValue = 'You have an active examination in progress. Leaving will forfeit your attempt.';
      return e.returnValue;
    }
  });

  // 6. Disable right-click context menu during exam
  document.addEventListener('contextmenu', (e) => {
    if (!viewExam.classList.contains('hidden')) {
      e.preventDefault();
    }
  });

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});

