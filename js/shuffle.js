/**
 * shuffle.js
 * Unbiased Fisher-Yates shuffling using cryptographic randomness where available.
 */

const Shuffle = (() => {
  /**
   * Generates a random integer in [0, maxExclusive) using crypto if available
   */
  function getRandomInt(maxExclusive) {
    if (maxExclusive <= 1) return 0;
    if (window.crypto && window.crypto.getRandomValues) {
      const array = new Uint32Array(1);
      const maxUint32 = 0xFFFFFFFF;
      const limit = maxUint32 - (maxUint32 % maxExclusive);
      let rand;
      do {
        window.crypto.getRandomValues(array);
        rand = array[0];
      } while (rand >= limit);
      return rand % maxExclusive;
    }
    return Math.floor(Math.random() * maxExclusive);
  }

  /**
   * Fisher-Yates array shuffle (returns a new shuffled array)
   */
  function shuffleArray(arr) {
    const copy = [...arr];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = getRandomInt(i + 1);
      const temp = copy[i];
      copy[i] = copy[j];
      copy[j] = temp;
    }
    return copy;
  }

  /**
   * Shuffles question options while ensuring option IDs ('A', 'B', 'C', 'D')
   * retain their immutable identity and correct mapping.
   */
  function shuffleOptions(options) {
    return shuffleArray(options);
  }

  return {
    shuffleArray,
    shuffleOptions,
    getRandomInt
  };
})();

