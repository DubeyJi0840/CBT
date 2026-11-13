/**
 * timer.js
 * Absolute-deadline countdown timer for CBT examinations.
 * Resilient against browser throttling, tab suspension, and refresh.
 */

class ExamTimer {
  constructor(deadlineTimestamp, onTick, onTimeout) {
    this.deadline = deadlineTimestamp;
    this.onTick = onTick;
    this.onTimeout = onTimeout;
    this.intervalId = null;
    this.isExpired = false;
  }

  start() {
    this.stop();
    this.isExpired = false;
    this.tick();
    this.intervalId = setInterval(() => this.tick(), 1000);
  }

  tick() {
    const now = Date.now();
    const remainingMs = this.deadline - now;

    if (remainingMs <= 0) {
      this.isExpired = true;
      this.stop();
      if (typeof this.onTick === 'function') {
        this.onTick('00:00:00', 0, 'expired');
      }
      if (typeof this.onTimeout === 'function') {
        this.onTimeout();
      }
      return;
    }

    const totalSeconds = Math.floor(remainingMs / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const pad = (n) => String(n).padStart(2, '0');
    const formatted = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;

    let urgency = 'normal';
    if (totalSeconds <= 300) {
      urgency = 'critical'; // under 5 mins
    } else if (totalSeconds <= 900) {
      urgency = 'warning'; // under 15 mins
    }

    if (typeof this.onTick === 'function') {
      this.onTick(formatted, totalSeconds, urgency);
    }
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  getRemainingSeconds() {
    const remainingMs = this.deadline - Date.now();
    return Math.max(0, Math.floor(remainingMs / 1000));
  }
}

