/**
 * results.js
 * Renders the candidate examination score card and performance analytics.
 */

const ResultsDashboard = (() => {
  function render(resultData, containerEl) {
    if (!resultData || !containerEl) return;

    const timeFormatted = formatSeconds(resultData.timeTakenSeconds);
    const scoreColorClass = resultData.finalScore >= 40 ? 'score-pass' : 'score-fail';

    containerEl.innerHTML = `
      <div class="result-card">
        <div class="result-header">
          <div class="result-badge-official">OFFICIAL CBT SCORE CARD</div>
          <h2>LIS CBT Practice Examination Result</h2>
          <p class="attempt-meta">Attempt ID: <code>${resultData.attemptId}</code> | Date: ${new Date(resultData.submittedAt).toLocaleString()}</p>
          ${resultData.isAutoSubmit ? '<div class="alert-banner alert-warning">Notice: Time expired. Exam was automatically submitted.</div>' : ''}
        </div>

        <div class="score-summary-grid">
          <div class="score-hero-box ${scoreColorClass}">
            <div class="score-label">FINAL SCORE</div>
            <div class="score-big">${resultData.finalScore} <span class="score-max">/ ${resultData.maxScore}</span></div>
            <div class="score-subtext">${resultData.finalScore >= 40 ? 'Qualified / Above Benchmark' : 'Needs Practice'}</div>
          </div>

          <div class="stat-mini-card">
            <div class="stat-label">Accuracy</div>
            <div class="stat-value text-blue">${resultData.accuracy}%</div>
            <div class="stat-subtext">Correct / Attempted</div>
          </div>

          <div class="stat-mini-card">
            <div class="stat-label">Time Taken</div>
            <div class="stat-value">${timeFormatted}</div>
            <div class="stat-subtext">out of 90:00 mins</div>
          </div>
        </div>

        <div class="marks-breakdown-panel">
          <h3>Marking Scheme & Statistics Breakdown</h3>
          <div class="breakdown-grid">
            <div class="breakdown-item bg-light-blue">
              <span class="b-label">Total Questions</span>
              <span class="b-val">${resultData.totalQuestions}</span>
            </div>
            <div class="breakdown-item bg-light-purple">
              <span class="b-label">Total Attempted</span>
              <span class="b-val">${resultData.attempted}</span>
            </div>
            <div class="breakdown-item bg-light-green">
              <span class="b-label">Correct (+1.0 mark)</span>
              <span class="b-val text-green">${resultData.correct}</span>
            </div>
            <div class="breakdown-item bg-light-red">
              <span class="b-label">Incorrect (-0.25 mark)</span>
              <span class="b-val text-red">${resultData.incorrect}</span>
            </div>
            <div class="breakdown-item bg-light-gray">
              <span class="b-label">Unattempted (0.0 marks)</span>
              <span class="b-val text-muted">${resultData.unattempted}</span>
            </div>
            <div class="breakdown-item bg-light-green">
              <span class="b-label">Positive Marks</span>
              <span class="b-val text-green">+${resultData.positiveMarks}</span>
            </div>
            <div class="breakdown-item bg-light-red">
              <span class="b-label">Negative Marks</span>
              <span class="b-val text-red">-${resultData.negativeMarks}</span>
            </div>
            <div class="breakdown-item bg-light-gold">
              <span class="b-label">Net Score</span>
              <span class="b-val"><strong>${resultData.finalScore}</strong></span>
            </div>
          </div>
        </div>

        <div class="result-actions-bar">
          <button id="btn-review-answers" class="btn btn-primary btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            Review Detailed Answers
          </button>
          <button id="btn-retake-exam" class="btn btn-secondary btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            Start New Attempt (Fresh 100 Questions)
          </button>
          <button id="btn-result-home" class="btn btn-outline btn-lg">
            Back to Instructions
          </button>
        </div>
      </div>
    `;
  }

  function formatSeconds(secs) {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(mins).padStart(2, '0')}:${String(s).padStart(2, '0')} min`;
  }

  return {
    render
  };
})();

