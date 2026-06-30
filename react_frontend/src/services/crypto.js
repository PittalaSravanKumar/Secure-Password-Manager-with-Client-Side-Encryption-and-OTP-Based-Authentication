import CryptoJS from 'crypto-js';

// Get encryption key from environment variable or use a fallback for MVP
const ENCRYPTION_KEY = import.meta.env.VITE_ENCRYPTION_KEY || 'default-secure-key-123';

/**
 * Encrypts a string using AES encryption
 * @param {string} text - The plaintext to encrypt
 * @returns {string} The encrypted text
 */
export const encryptText = (text) => {
  if (!text) return '';
  return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
};

/**
 * Decrypts an AES encrypted string
 * @param {string} cipherText - The encrypted text
 * @returns {string} The decrypted plaintext
 */
export const decryptText = (cipherText) => {
  if (!cipherText) return '';
  try {
    const bytes = CryptoJS.AES.decrypt(cipherText, ENCRYPTION_KEY);
    return bytes.toString(CryptoJS.enc.Utf8);
  } catch (error) {
    console.error('Error decrypting text:', error);
    return 'Decryption Error';
  }
};
