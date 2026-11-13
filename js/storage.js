/**
 * storage.js
 * Manages CBT session persistence and completed results using localStorage.
 */

const Storage = (() => {
  const SESSION_KEY = 'lis_cbt_active_session_v1';
  const RESULT_KEY = 'lis_cbt_last_result_v1';

  function saveSession(sessionData) {
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
      return true;
    } catch (e) {
      console.warn('Failed to save session to localStorage', e);
      return false;
    }
  }

  function getSession() {
    try {
      const data = localStorage.getItem(SESSION_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.warn('Failed to read session from localStorage', e);
      return null;
    }
  }

  function clearSession() {
    try {
      localStorage.removeItem(SESSION_KEY);
      return true;
    } catch (e) {
      console.warn('Failed to clear session', e);
      return false;
    }
  }

  function saveResult(resultData) {
    try {
      localStorage.setItem(RESULT_KEY, JSON.stringify(resultData));
      return true;
    } catch (e) {
      console.warn('Failed to save result to localStorage', e);
      return false;
    }
  }

  function getLastResult() {
    try {
      const data = localStorage.getItem(RESULT_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.warn('Failed to read result from localStorage', e);
      return null;
    }
  }

  function clearResult() {
    try {
      localStorage.removeItem(RESULT_KEY);
      return true;
    } catch (e) {
      console.warn('Failed to clear result', e);
      return false;
    }
  }

  return {
    saveSession,
    getSession,
    clearSession,
    saveResult,
    getLastResult,
    clearResult
  };
})();

