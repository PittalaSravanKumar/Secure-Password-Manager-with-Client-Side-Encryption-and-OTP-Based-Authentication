self.cachedMasterKey = null;
self.sessionTimeout = null;

// Convert Base64 to Buffer
function base64ToBuffer(b64) {
    const binary_string = self.atob(b64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) { bytes[i] = binary_string.charCodeAt(i); }
    return bytes.buffer;
}

// Convert Buffer to Base64
function bufferToBase64(buf) {
    let binary = '';
    const bytes = new Uint8Array(buf);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return self.btoa(binary);
}

// Web Crypto PBKDF2 function
async function deriveAESKey(masterKey, saltBuffer) {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        "raw", enc.encode(masterKey), { name: "PBKDF2" }, false, ["deriveBits", "deriveKey"]
    );
    return crypto.subtle.deriveKey(
        { name: "PBKDF2", salt: saltBuffer, iterations: 600000, hash: "SHA-256" },
        keyMaterial, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]
    );
}

function startSessionTimer() {
    if (self.sessionTimeout) clearTimeout(self.sessionTimeout);
    // 15 minutes = 900,000 ms
    self.sessionTimeout = setTimeout(() => {
        self.cachedMasterKey = null; // Wipe the key from memory
        postMessage({ type: 'SESSION_EXPIRED' });
    }, 900000); 
}

// Listen for messages from the main UI thread
self.onmessage = async function(e) {
    const { type, payload } = e.data;

    try {
        if (type === 'INIT_SESSION') {
            // UI sends the Master Key just once to initialize the worker
            const { masterKey } = payload;
            if (!masterKey) throw new Error("Attempted to init session with empty master key.");
            self.cachedMasterKey = masterKey;
            startSessionTimer();
            postMessage({ type: 'SESSION_STARTED' });
        } 
        
        else if (type === 'ENCRYPT_PAYLOAD') {
            if (!self.cachedMasterKey) throw new Error("No active session. Please provide Master Key.");
            
            const { plaintextData } = payload;
            
            // 1. Generate Salt and Nonce
            const salt = crypto.getRandomValues(new Uint8Array(16));
            const nonce = crypto.getRandomValues(new Uint8Array(12));

            // 2. Derive Key based on generated Salt
            const aesKey = await deriveAESKey(self.cachedMasterKey, salt);
            
            const enc = new TextEncoder();
            const ciphertext = await crypto.subtle.encrypt(
                { name: "AES-GCM", iv: nonce }, aesKey, enc.encode(JSON.stringify(plaintextData))
            );

            startSessionTimer();
            postMessage({ 
                type: 'ENCRYPT_SUCCESS', 
                payload: {
                    ciphertextBase64: bufferToBase64(ciphertext),
                    saltBase64: bufferToBase64(salt),
                    nonceBase64: bufferToBase64(nonce)
                } 
            });
        }

        else if (type === 'DECRYPT_PAYLOAD') {
            if (!self.cachedMasterKey) throw new Error("No active session. Please provide Master Key.");
            
            const { ciphertextBase64, nonceBase64, saltBase64 } = payload;
            
            const cipherBuffer = base64ToBuffer(ciphertextBase64);
            const nonceBuffer = base64ToBuffer(nonceBase64);
            const saltBuffer = base64ToBuffer(saltBase64);

            const aesKey = await deriveAESKey(self.cachedMasterKey, saltBuffer);

            const decryptedBuffer = await crypto.subtle.decrypt(
                { name: "AES-GCM", iv: nonceBuffer },
                aesKey,
                cipherBuffer
            );

            const dec = new TextDecoder();
            const plaintextData = JSON.parse(dec.decode(decryptedBuffer));
            
            // Reset the 15-minute timer every time they successfully decrypt something
            startSessionTimer(); 
            postMessage({ type: 'DECRYPT_SUCCESS', payload: plaintextData });
        }
        
        else if (type === 'LOCK_VAULT') {
            self.cachedMasterKey = null;
            if (self.sessionTimeout) clearTimeout(self.sessionTimeout);
            postMessage({ type: 'VAULT_LOCKED' });
        }
    } catch (error) {
        postMessage({ type: 'ERROR', error: error.message, originalType: type });
    }
};
