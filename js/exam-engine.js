/**
 * exam-engine.js
 * Core state machine and scoring engine for LIS CBT Examination.
 */

class ExamEngine {
  constructor() {
    this.attemptId = null;
    this.questions = [];
    this.optionOrders = {}; // { qId: [shuffled option objects] }
    this.userAnswers = {};  // { qIndex: selectedOptionId }
    this.reviewFlags = {};  // { qIndex: boolean }
    this.visited = {};      // { qIndex: boolean }
    this.currentIndex = 0;
    this.startTime = null;
    this.deadline = null;
    this.submitted = false;
    this.durationMinutes = 90;
    this.timer = null;
    this.onStateChange = null;
  }

  /**
   * Initializes a fresh exam attempt with newly shuffled questions & options.
   */
  startNewExam(count = 100) {
    const rawQuestions = QuestionBank.selectRandomQuestions(count);
    this.attemptId = 'LIS-' + Date.now() + '-' + Shuffle.getRandomInt(10000);
    this.questions = rawQuestions;
    this.optionOrders = {};
    this.userAnswers = {};
    this.reviewFlags = {};
    this.visited = { 0: true }; // First question visited immediately
    this.currentIndex = 0;
    this.startTime = Date.now();
    this.deadline = this.startTime + (this.durationMinutes * 60 * 1000);
    this.submitted = false;

    // Shuffle options for each question independently, maintaining immutable option IDs
    for (const q of this.questions) {
      this.optionOrders[q.id] = Shuffle.shuffleOptions(q.options);
    }

    this.persist();
    return this.getState();
  }

  /**
   * Resumes an existing active session from stored data without reshuffling.
   */
  resumeExam(savedSession) {
    this.attemptId = savedSession.attemptId;
    this.questions = savedSession.questions;
    this.optionOrders = savedSession.optionOrders;
    this.userAnswers = savedSession.userAnswers || {};
    this.reviewFlags = savedSession.reviewFlags || {};
    this.visited = savedSession.visited || {};
    this.currentIndex = typeof savedSession.currentIndex === 'number' ? savedSession.currentIndex : 0;
    this.startTime = savedSession.startTime;
    this.deadline = savedSession.deadline;
    this.submitted = Boolean(savedSession.submitted);
    this.visited[this.currentIndex] = true;

    this.persist();
    return this.getState();
  }

  getCurrentQuestion() {
    if (!this.questions || this.questions.length === 0) return null;
    const q = this.questions[this.currentIndex];
    const options = this.optionOrders[q.id] || q.options;
    const selected = this.userAnswers[this.currentIndex] || null;
    const isMarked = Boolean(this.reviewFlags[this.currentIndex]);

    return {
      index: this.currentIndex,
      questionNumber: this.currentIndex + 1,
      totalQuestions: this.questions.length,
      data: q,
      shuffledOptions: options,
      selectedOption: selected,
      isMarkedForReview: isMarked
    };
  }

  navigateTo(index) {
    if (index < 0 || index >= this.questions.length) return;
    this.currentIndex = index;
    this.visited[index] = true;
    this.persist();
    if (this.onStateChange) this.onStateChange(this.getState());
  }

  saveAndNext(selectedOptionId) {
    if (selectedOptionId) {
      this.userAnswers[this.currentIndex] = selectedOptionId;
    }
    // Remove review flag if saving answer normally
    delete this.reviewFlags[this.currentIndex];
    this.visited[this.currentIndex] = true;

    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
      this.visited[this.currentIndex] = true;
    }
    this.persist();
    if (this.onStateChange) this.onStateChange(this.getState());
  }

  markForReviewAndNext(selectedOptionId) {
    if (selectedOptionId) {
      this.userAnswers[this.currentIndex] = selectedOptionId;
    }
    this.reviewFlags[this.currentIndex] = true;
    this.visited[this.currentIndex] = true;

    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
      this.visited[this.currentIndex] = true;
    }
    this.persist();
    if (this.onStateChange) this.onStateChange(this.getState());
  }

  clearResponse() {
    delete this.userAnswers[this.currentIndex];
    delete this.reviewFlags[this.currentIndex];
    this.visited[this.currentIndex] = true;
    this.persist();
    if (this.onStateChange) this.onStateChange(this.getState());
  }

  getQuestionStatus(index) {
    const isVisited = Boolean(this.visited[index]);
    const hasAnswer = Boolean(this.userAnswers[index]);
    const isMarked = Boolean(this.reviewFlags[index]);

    if (!isVisited) return 'not-visited';
    if (isMarked && hasAnswer) return 'answered-marked';
    if (isMarked && !hasAnswer) return 'marked';
    if (hasAnswer) return 'answered';
    return 'not-answered';
  }

  getSummaryCounts() {
    let answered = 0;
    let notAnswered = 0;
    let marked = 0;
    let answeredMarked = 0;
    let notVisited = 0;

    for (let i = 0; i < this.questions.length; i++) {
      const status = this.getQuestionStatus(i);
      switch (status) {
        case 'answered': answered++; break;
        case 'not-answered': notAnswered++; break;
        case 'marked': marked++; break;
        case 'answered-marked': answeredMarked++; break;
        case 'not-visited': notVisited++; break;
      }
    }

    return {
      total: this.questions.length,
      answered,
      notAnswered,
      marked,
      answeredMarked,
      notVisited,
      attempted: answered + answeredMarked
    };
  }

  /**
   * Submits the active exam attempt and calculates final scores.
   * Scoring formula: Score = (Correct * 1) - (Incorrect * 0.25).
   * Accuracy = (Correct / Attempted) * 100, or 0 if attempted is zero.
   */
  submitExam(isAutoSubmit = false) {
    if (this.submitted) {
      return Storage.getLastResult();
    }

    this.submitted = true;
    const timeTakenSeconds = Math.min(
      this.durationMinutes * 60,
      Math.max(0, Math.floor((Date.now() - this.startTime) / 1000))
    );

    let correctCount = 0;
    let incorrectCount = 0;
    let unattemptedCount = 0;

    const questionAnalysis = [];

    for (let i = 0; i < this.questions.length; i++) {
      const q = this.questions[i];
      const selected = this.userAnswers[i] || null;
      const verifiedCorrect = q.correct_option;
      const options = this.optionOrders[q.id] || q.options;

      let status = 'unattempted';
      let marksAwarded = 0;

      if (selected !== null && selected !== undefined) {
        if (selected === verifiedCorrect) {
          correctCount++;
          status = 'correct';
          marksAwarded = 1.0;
        } else {
          incorrectCount++;
          status = 'incorrect';
          marksAwarded = -0.25;
        }
      } else {
        unattemptedCount++;
        status = 'unattempted';
        marksAwarded = 0.0;
      }

      questionAnalysis.push({
        index: i,
        questionNumber: i + 1,
        questionId: q.id,
        question: q.question,
        questionEn: q.question_en,
        questionHi: q.question_hi,
        options: options,
        selectedOption: selected,
        correctOption: verifiedCorrect,
        status: status,
        marks: marksAwarded,
        sourceFile: q.source_file,
        sourcePage: q.source_page,
        originalQno: q.original_question_number
      });
    }

    const positiveMarks = correctCount * 1.0;
    const negativeMarks = incorrectCount * 0.25;
    const finalScore = positiveMarks - negativeMarks;
    const totalAttempted = correctCount + incorrectCount;
    const accuracy = totalAttempted > 0 ? (correctCount / totalAttempted) * 100 : 0;

    const result = {
      attemptId: this.attemptId,
      submittedAt: new Date().toISOString(),
      isAutoSubmit: isAutoSubmit,
      durationMinutes: this.durationMinutes,
      timeTakenSeconds: timeTakenSeconds,
      totalQuestions: this.questions.length,
      attempted: totalAttempted,
      correct: correctCount,
      incorrect: incorrectCount,
      unattempted: unattemptedCount,
      positiveMarks: Number(positiveMarks.toFixed(2)),
      negativeMarks: Number(negativeMarks.toFixed(2)),
      finalScore: Number(finalScore.toFixed(2)),
      maxScore: this.questions.length,
      accuracy: Number(accuracy.toFixed(2)),
      questionAnalysis: questionAnalysis
    };

    Storage.saveResult(result);
    Storage.clearSession();

    return result;
  }

  persist() {
    Storage.saveSession({
      attemptId: this.attemptId,
      questions: this.questions,
      optionOrders: this.optionOrders,
      userAnswers: this.userAnswers,
      reviewFlags: this.reviewFlags,
      visited: this.visited,
      currentIndex: this.currentIndex,
      startTime: this.startTime,
      deadline: this.deadline,
      submitted: this.submitted
    });
  }

  getState() {
    return {
      attemptId: this.attemptId,
      currentQuestion: this.getCurrentQuestion(),
      summary: this.getSummaryCounts(),
      deadline: this.deadline,
      submitted: this.submitted
    };
  }
}

