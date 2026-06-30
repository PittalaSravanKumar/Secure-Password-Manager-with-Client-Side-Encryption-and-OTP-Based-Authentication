from flask import Flask, render_template, request, jsonify, session
import random
import string
import pandas as pd
import os
import re
from datetime import datetime

# Import custom modules
from firebase_utils import UserDatabase
from email_utils import send_otp, send_wrong_password_alert
from crypting import (
    encrypt_with_email_6char, 
    decrypt_with_email_6char,
    encrypt_with_email_8char,
    decrypt_with_email_8char,
    get_algorithm_remainder,
    extract_key
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database
db = UserDatabase()

# Excel file for sample login/registration
EXCEL_FILE = 'sample_users.xlsx'

def init_excel():
    """Initialize Excel file if it doesn't exist"""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=['FirstName', 'LastName', 'UserID', 'Email', 'Password'])
        df.to_excel(EXCEL_FILE, index=False)

init_excel()

def generate_random_code(length=6):
    """Generate random alphanumeric code"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_password(length=8):
    """Generate random password with letters, digits, and special characters"""
    letters = string.ascii_letters
    digits = string.digits
    special = '!@#$%^&*'
    
    # Ensure at least one of each type
    password = [
        random.choice(letters),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill the rest randomly
    all_chars = letters + digits + special
    password.extend(random.choices(all_chars, k=length - 3))
    
    # Shuffle to avoid predictable patterns
    random.shuffle(password)
    return ''.join(password)

# Routes for HTML pages
@app.route('/')
def index():
    return render_template('sample_registration.html')

@app.route('/sample_registration.html')
def sample_registration_page():
    return render_template('sample_registration.html')

@app.route('/sample_login.html')
def sample_login_page():
    return render_template('sample_login.html')

@app.route('/main_registration.html')
def main_registration_page():
    return render_template('main_registration.html')

@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/main_dashboard.html')
def main_dashboard_page():
    return render_template('main_dashboard.html')

@app.route('/crypto_dashboard.html')
def crypto_dashboard_page():
    if not session.get('logged_in'):
        return render_template('sample_login.html')
    return render_template('crypto_dashboard.html')


# API Endpoints

@app.route('/send_sample_registration_otp', methods=['POST'])
def send_sample_registration_otp():
    """Send OTP for sample registration to verify email"""
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})
            
        if not db.user_exists(email):
            return jsonify({'success': False, 'message': 'User does not exist in main database'})
            
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        
        # Send OTP via email
        if send_otp(email, otp):
            session[f'sample_otp_{email}'] = otp
            return jsonify({'success': True, 'message': 'OTP sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sample_register', methods=['POST'])
def sample_register():
    """Handle sample registration form submission"""
    try:
        data = request.json
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        user_id = data.get('userId')
        email = data.get('email')
        password = data.get('password')
        save_to_database = data.get('saveToDatabase', False)
        verification_email = data.get('verificationEmail')
        verification_code = data.get('verificationCode')
        verification_otp = data.get('verificationOtp')
        
        # Validate password length
        if len(password) != 8:
            return jsonify({'success': False, 'message': 'Password must be exactly 8 characters'})
        
        # Validate password contains letters, digits, and special characters
        has_letter = bool(re.search(r'[a-zA-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password))
        
        if not (has_letter and has_digit and has_special):
            return jsonify({
                'success': False, 
                'message': 'Password must contain letters, digits, and special characters'
            })
        
        # Read existing Excel data
        df = pd.read_excel(EXCEL_FILE)
        
        # Check if user ID already exists
        if user_id in df['UserID'].values:
            return jsonify({'success': False, 'message': 'User ID already exists'})
        
        # Add new user to Excel (always save to Excel)
        new_user = pd.DataFrame([{
            'FirstName': first_name,
            'LastName': last_name,
            'UserID': user_id,
            'Email': email,
            'Password': password
        }])
        
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)
        
        # If user wants to save to database, verify and save
        if save_to_database and verification_email and verification_code and verification_otp:
            # Verify OTP first
            stored_otp = session.get(f'sample_otp_{verification_email}')
            if not stored_otp or stored_otp != verification_otp:
                return jsonify({'success': False, 'message': 'Invalid OTP'})
                
            if not db.user_exists(verification_email):
                return jsonify({'success': False, 'message': 'User does not exist in main database'})
            
            # Get user data
            user_data = db.get_particular_user(verification_email)
            
            if user_data['email'] == 0:
                return jsonify({'success': False, 'message': 'User does not exist in main database'})
            
            # Decrypt stored code
            encrypted_code = user_data['code']
            try:
                decrypted_code = decrypt_with_email_6char(verification_email, encrypted_code)
                
                # Verify code
                if decrypted_code == verification_code:
                    # Encrypt password and store in database
                    encrypted_password = encrypt_with_email_8char(verification_email, password)
                    website_title = 'Sample Registration'
                    
                    # Update user in database
                    update_result = db.update_user(verification_email, website=website_title, password=encrypted_password)
                    
                    if update_result.get('success'):
                        return jsonify({'success': True, 'message': 'Registration successful and saved to main database'})
                    else:
                        return jsonify({'success': False, 'message': 'Registration failed: ' + update_result.get('error', 'Unknown error')})
                else:
                    # Code doesn't match - send alert
                    send_wrong_password_alert(verification_email)
                    return jsonify({
                        'success': False, 
                        'message': 'Invalid code',
                        'alert_sent': True
                    })
            
            except Exception as e:
                send_wrong_password_alert(verification_email)
                return jsonify({
                    'success': False, 
                    'message': 'Error verifying code',
                    'alert_sent': True
                })
        
        # If not saving to database or closed popup, just return success
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sample_login', methods=['POST'])
def sample_login():
    """Handle sample login form submission"""
    try:
        data = request.json
        user_id = data.get('userId')
        password = data.get('password')
        
        # Read Excel data
        df = pd.read_excel(EXCEL_FILE)
        
        # Check if user exists
        user_row = df[df['UserID'] == user_id]
        
        if user_row.empty:
            return jsonify({'success': False, 'message': 'User not registered'})
        
        # Verify password
        if user_row.iloc[0]['Password'] == password:
            # Set session so crypto_dashboard.html / protected routes work
            session['logged_in'] = True
            session['email'] = str(user_row.iloc[0]['Email'])
            session['name'] = str(user_row.iloc[0]['FirstName']) + ' ' + str(user_row.iloc[0]['LastName'])
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Wrong password'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_suggested_password', methods=['POST'])
def get_suggested_password():
    """Generate and return a suggested password after verification"""
    try:
        data = request.json
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'success': False, 'message': 'Email and code are required'})
        
        # Check if user exists
        if not db.user_exists(email):
            return jsonify({'success': False, 'message': 'User does not exist'})
        
        # Get user data
        user_data = db.get_particular_user(email)
        
        if user_data['email'] == 0:
            return jsonify({'success': False, 'message': 'User does not exist'})
        
        # Decrypt stored code
        encrypted_code = user_data['code']
        try:
            decrypted_code = decrypt_with_email_6char(email, encrypted_code)
            
            #
            if decrypted_code == code:
                # Generate random 8-character password
                random_password = generate_random_password(8)
                
                return jsonify({
                    'success': True, 
                    'password': random_password
                })
            else:
                # Code doesn't match - send alert and close popup
                send_wrong_password_alert(email)
                return jsonify({
                    'success': False, 
                    'message': 'Invalid code',
                    'alert_sent': True
                })
        
        except Exception as e:
            send_wrong_password_alert(email)
            return jsonify({
                'success': False, 
                'message': 'Error verifying code',
                'alert_sent': True
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/verify_and_decrypt', methods=['POST'])
def verify_and_decrypt():
    """Autofill password: verify security code via Firebase (if available), then return password from Excel."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({'success': False, 'message': 'Email and code are required'})

        user_name = 'User'

        # ── Step 1: Try to verify the security code via Firebase ──────────────
        # This is optional: if Firebase is unreachable or user not registered
        # there, we skip code verification and still serve from Excel.
        firebase_code_checked = False
        try:
            if db.user_exists(email):
                user_data = db.get_particular_user(email)
                if user_data and user_data.get('email') != 0:
                    user_name = user_data.get('name', 'User')
                    encrypted_code = user_data.get('code', '')
                    if encrypted_code:
                        decrypted_code = decrypt_with_email_6char(email, encrypted_code)
                        firebase_code_checked = True
                        if decrypted_code != code:
                            # Wrong code — send alert and reject
                            send_wrong_password_alert(email)
                            return jsonify({
                                'success': False,
                                'message': 'Invalid security code',
                                'alert_sent': True
                            })
        except Exception:
            # Firebase unavailable — proceed without code verification
            pass

        # ── Step 2: Always fetch the password from Excel ──────────────────────
        try:
            df = pd.read_excel(EXCEL_FILE)
            # Case-insensitive match on Email column
            user_row = df[df['Email'].astype(str).str.strip().str.lower() == email]
            if not user_row.empty:
                plain_password = str(user_row.iloc[0]['Password'])
                # Set session
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user_name
                return jsonify({'success': True, 'password': plain_password})
            else:
                return jsonify({
                    'success': False,
                    'message': 'No account found with this email in the system'
                })
        except Exception as ex:
            return jsonify({'success': False, 'message': 'Error reading user data: ' + str(ex)})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/send_registration_otp', methods=['POST'])
def send_registration_otp():
    """Send OTP for main registration"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()  # normalize to lowercase
        name = data.get('name')
        
        if not email or not name:
            return jsonify({'success': False, 'message': 'Email and name are required'})
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        
        # Send OTP via email
        if send_otp(email, otp):
            # Store OTP in session for verification
            session[f'otp_{email}'] = otp
            session[f'name_{email}'] = name
            
            return jsonify({
                'success': True, 
                'message': 'OTP sent successfully',
                'otp': otp  # In production, don't send OTP in response
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/complete_registration', methods=['POST'])
def complete_registration():
    """Complete main registration after OTP verification"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()  # CRITICAL: normalize so encryption key matches decryption key at login
        name = data.get('name')
        
        if not email or not name:
            return jsonify({'success': False, 'message': 'Email and name are required'})
        
        # Generate 6-character code
        code = generate_random_code(6)
        
        # Encrypt code
        encrypted_code = encrypt_with_email_6char(email, code)
        
        # Check if user exists
        if db.user_exists(email):
            # Update existing user with new encrypted code
            result = db.update_user(email, name=name, code=encrypted_code)
            
            if result['success']:
                return jsonify({
                    'success': True, 
                    'message': 'Code updated successfully',
                    'code': code
                })
            else:
                return jsonify({'success': False, 'message': result['error']})
        else:
            # Add new user
            result = db.add_user(email, name, encrypted_code, '0', '0')
            
            if result['success']:
                return jsonify({
                    'success': True, 
                    'message': 'Registration successful',
                    'code': code
                })
            else:
                return jsonify({'success': False, 'message': result['error']})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get_user_crypto_info', methods=['GET'])
def get_user_crypto_info():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    email = session.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email not found in session'}), 400

    try:
        # Determine 6-character cipher
        remainder_6 = get_algorithm_remainder(email, 6)
        ciphers_6 = {
            0: "AES-CTR (HMAC)",
            1: "Camellia-CBC (HMAC)",
            2: "AES-GCM",
            3: "XChaCha20-Poly1305",
            4: "ChaCha20-Poly1305",
            5: "Salsa20"
        }
        cipher_6_name = ciphers_6.get(remainder_6, "Unknown")

        # Determine 8-character cipher
        remainder_5 = get_algorithm_remainder(email, 5)
        ciphers_5 = {
            0: "AES-CTR (HMAC)",
            1: "Camellia-CBC (HMAC)",
            2: "AES-GCM",
            3: "XChaCha20-Poly1305",
            4: "ChaCha20-Poly1305"
        }
        cipher_8_name = ciphers_5.get(remainder_5, "Unknown")
        
        # Get extracted key visualization
        seed_key_6 = extract_key(email, 6)
        seed_key_8 = extract_key(email, 8)

        return jsonify({
            'success': True,
            'email': email,
            'name': session.get('name', 'User'),
            'seed_key_6': seed_key_6,
            'seed_key_8': seed_key_8,
            'cipher_6_char': cipher_6_name,
            'cipher_8_char': cipher_8_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

import time

# Rate limiting storage for vault failures
# Structure: { email: { 'attempts': [timestamps], 'lockout_until': timestamp } }
vault_auth_limit_store = {}

@app.route('/api/vault/save', methods=['POST'])
def save_vault_entry():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    email = session.get('email')
    data = request.json
    
    result = db.add_vault_entry(email, data)
    if result['success']:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': result['error']}), 500

@app.route('/api/vault/entries', methods=['GET'])
def get_vault_entries():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    email = session.get('email')
    result = db.get_vault_entries(email)
    
    if result['success']:
        return jsonify({'success': True, 'entries': result['data']})
    else:
        return jsonify({'success': False, 'message': result['error']}), 500

@app.route('/api/vault/delete/<entry_id>', methods=['DELETE'])
def delete_vault_entry(entry_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    email = session.get('email')
    result = db.delete_vault_entry(email, entry_id)

    if result['success']:
        return jsonify({'success': True, 'message': 'Entry deleted successfully'})
    else:
        return jsonify({'success': False, 'message': result['error']}), 500

@app.route('/api/vault_auth_failure', methods=['POST'])
def vault_auth_failure():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
    email = session.get('email')
    current_time = time.time()
    
    if email not in vault_auth_limit_store:
        vault_auth_limit_store[email] = {'attempts': [], 'lockout_until': 0}
        
    store = vault_auth_limit_store[email]
    
    # Check if currently locked out
    if current_time < store['lockout_until']:
        return jsonify({'success': False, 'message': 'Vault locked due to excessive failed attempts. Please try again later.', 'locked': True}), 429
        
    # Filter attempts in the last 15 minutes (900 seconds)
    store['attempts'] = [t for t in store['attempts'] if current_time - t <= 900]
    
    # Register new attempt
    store['attempts'].append(current_time)
    
    if len(store['attempts']) >= 4:
        # Lockout for 1 hour (3600 seconds)
        store['lockout_until'] = current_time + 3600
        return jsonify({'success': False, 'message': 'Vault locked due to excessive failed attempts. Please try again later.', 'locked': True}), 429
        
    # Still under threshold, send the alert email
    # Utilizing existing email utility
    try:
        send_wrong_password_alert(email)
    except Exception as e:
        print("Failed to send alert email:", str(e))
        
    return jsonify({'success': True, 'message': 'Alert dispatched'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)