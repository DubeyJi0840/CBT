/**
 * review.js
 * Renders the question-by-question answer review with candidate responses,
 * verified answers from source PDFs, and interactive status filters.
 */

const AnswerReview = (() => {
  let currentResult = null;
  let currentFilter = 'all';

  function render(resultData, containerEl) {
    if (!resultData || !containerEl) return;
    currentResult = resultData;

    containerEl.innerHTML = `
      <div class="review-page">
        <div class="review-header-bar">
          <div>
            <h2>Detailed Answer Key & Question Analysis</h2>
            <p class="review-submeta">Attempt ID: <code>${resultData.attemptId}</code> | Verified Source: Official Printed Answer Keys</p>
          </div>
          <div class="review-header-actions">
            <button id="btn-back-to-dashboard" class="btn btn-secondary">
              Back to Score Card
            </button>
            <button id="btn-review-retake" class="btn btn-primary">
              Retake Exam
            </button>
          </div>
        </div>

        <div class="review-filter-bar">
          <span class="filter-label">Filter Questions:</span>
          <button class="filter-btn active" data-filter="all">All (${resultData.totalQuestions})</button>
          <button class="filter-btn text-green" data-filter="correct">Correct (${resultData.correct})</button>
          <button class="filter-btn text-red" data-filter="incorrect">Incorrect (${resultData.incorrect})</button>
          <button class="filter-btn text-muted" data-filter="unattempted">Unattempted (${resultData.unattempted})</button>
        </div>

        <div id="review-list-container" class="review-questions-list"></div>
      </div>
    `;

    renderQuestionList();
    attachFilterEvents();
  }

  function renderQuestionList() {
    const listEl = document.getElementById('review-list-container');
    if (!listEl || !currentResult) return;

    const items = currentResult.questionAnalysis.filter(q => {
      if (currentFilter === 'all') return true;
      return q.status === currentFilter;
    });

    if (items.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state-box">
          <p>No questions match the filter "<strong>${currentFilter}</strong>".</p>
        </div>
      `;
      return;
    }

    let html = '';
    for (const q of items) {
      const statusBadge = getStatusBadge(q.status, q.marks);

      // Render options with styling
      let optionsHtml = '';
      for (const opt of q.options) {
        const isCandidateChoice = q.selectedOption === opt.id;
        const isVerifiedCorrect = q.correctOption === opt.id;

        let optClass = 'review-option-row';
        let markerBadge = '';

        if (isVerifiedCorrect && isCandidateChoice) {
          optClass += ' option-correct-selected';
          markerBadge = '<span class="opt-badge badge-green">✓ Your Answer (Correct)</span>';
        } else if (isVerifiedCorrect) {
          optClass += ' option-correct-unselected';
          markerBadge = '<span class="opt-badge badge-green">✓ Official Correct Answer</span>';
        } else if (isCandidateChoice) {
          optClass += ' option-wrong-selected';
          markerBadge = '<span class="opt-badge badge-red">✗ Your Answer (Incorrect)</span>';
        }

        optionsHtml += `
          <div class="${optClass}">
            <div class="opt-col-letter">(${opt.id})</div>
            <div class="opt-col-text">${escapeHtml(opt.text)}</div>
            <div class="opt-col-badge">${markerBadge}</div>
          </div>
        `;
      }

      html += `
        <div class="review-item-card status-border-${q.status}">
          <div class="review-item-header">
            <div class="review-item-title">
              <span class="qno-pill">Question ${q.questionNumber}</span>
              ${statusBadge}
            </div>
            <div class="review-source-ref">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>Source: <strong>${escapeHtml(q.sourceFile)}</strong> (Page ${q.sourcePage}, Orig. Q#${q.originalQno})</span>
            </div>
          </div>

          <div class="review-prompt">
            ${q.questionEn ? `<div class="prompt-en">${escapeHtml(q.questionEn)}</div>` : ''}
            ${q.questionHi ? `<div class="prompt-hi">${escapeHtml(q.questionHi)}</div>` : ''}
          </div>

          <div class="review-options-group">
            ${optionsHtml}
          </div>

          <div class="review-footer-info">
            <span class="meta-field">Candidate Selection: <strong>${q.selectedOption ? `Option (${q.selectedOption})` : 'Not Attempted'}</strong></span>
            <span class="meta-field">Verified Answer Key: <strong class="text-green">Option (${q.correctOption})</strong></span>
            <span class="meta-field">Marks: <strong class="${q.marks > 0 ? 'text-green' : q.marks < 0 ? 'text-red' : ''}">${q.marks > 0 ? '+' + q.marks : q.marks}</strong></span>
          </div>
        </div>
      `;
    }

    listEl.innerHTML = html;
  }

  function getStatusBadge(status, marks) {
    if (status === 'correct') {
      return '<span class="pill-status pill-correct">CORRECT (+1.00)</span>';
    } else if (status === 'incorrect') {
      return '<span class="pill-status pill-incorrect">INCORRECT (-0.25)</span>';
    }
    return '<span class="pill-status pill-unattempted">UNATTEMPTED (0.00)</span>';
  }

  function attachFilterEvents() {
    const filterBtns = document.querySelectorAll('.review-filter-bar .filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.getAttribute('data-filter');
        renderQuestionList();
      });
    });
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  return {
    render
  };
})();

