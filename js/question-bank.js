/**
 * question-bank.js
 * Loads verified questions from data/questions.json and provides access utilities.
 */

const QuestionBank = (() => {
  let bank = [];
  let isLoaded = false;

  async function loadQuestions() {
    if (isLoaded && bank.length > 0) {
      return bank;
    }

    try {
      // Relative path for GitHub Pages compatibility
      const response = await fetch('./data/questions.json');
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status} loading questions.json`);
      }
      bank = await response.json();
      isLoaded = true;
      console.log(`Successfully loaded ${bank.length} verified questions into bank.`);
      return bank;
    } catch (err) {
      console.error('Error fetching data/questions.json:', err);
      // If window.EMBEDDED_QUESTIONS is defined (as static fallback if running via direct file:// without server)
      if (window.EMBEDDED_QUESTIONS && Array.isArray(window.EMBEDDED_QUESTIONS)) {
        console.warn('Falling back to embedded questions bank.');
        bank = window.EMBEDDED_QUESTIONS;
        isLoaded = true;
        return bank;
      }
      throw err;
    }
  }

  function getQuestions() {
    return bank;
  }

  function getVerifiedCount() {
    return bank.length;
  }

  /**
   * Selects `count` random unique questions from the verified bank.
   * If bank has fewer questions than count, returns all available shuffled.
   */
  function selectRandomQuestions(count = 100) {
    if (!bank || bank.length === 0) {
      throw new Error('Question bank is empty. Load questions first.');
    }

    // Shuffled copy of the entire bank
    const shuffledBank = Shuffle.shuffleArray(bank);
    const selected = shuffledBank.slice(0, Math.min(count, shuffledBank.length));

    return selected;
  }

  return {
    loadQuestions,
    getQuestions,
    getVerifiedCount,
    selectRandomQuestions
  };
})();

