import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

def initialize_firebase():
    if not firebase_admin._apps:
        cred_dict = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

initialize_firebase()
db = firestore.client()

class UserDatabase:
    def __init__(self):
        self.collection = db.collection('users')
    
    def add_user(self, email, name, code, website, password):
        if len(password) > 500:
            return {"success": False, "error": "Password exceeds 500 characters"}
        
        try:
            doc_ref = self.collection.document(email)
            doc_ref.set({
                'name': name,
                'code': code,
                'website': website,
                'password': password
            })
            return {"success": True, "message": f"User {email} added successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def add_vault_entry(self, email, entry_data):
        try:
            vault_col = self.collection.document(email).collection('vault_entries')
            # Assuming entry_data contains entry_id
            entry_id = entry_data.get('entry_id')
            if not entry_id:
                return {"success": False, "error": "Missing entry_id"}
            vault_col.document(entry_id).set(entry_data)
            return {"success": True, "message": "Vault entry added successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def get_vault_entries(self, email):
        try:
            vault_col = self.collection.document(email).collection('vault_entries')
            docs = vault_col.stream()
            entries = []
            for doc in docs:
                entries.append(doc.to_dict())
            return {"success": True, "data": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_vault_entry(self, email, entry_id):
        try:
            vault_col = self.collection.document(email).collection('vault_entries')
            vault_col.document(entry_id).delete()
            return {"success": True, "message": f"Entry {entry_id} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user(self, email):
        try:
            doc = self.collection.document(email).get()
            if doc.exists:
                data = doc.to_dict()
                data['email'] = email
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_particular_user(self, email):
        try:
            doc = self.collection.document(email).get()
            if doc.exists:
                data = doc.to_dict()
                return {
                    'email': email,
                    'name': data.get('name', ''),
                    'code': data.get('code', ''),
                    'website': data.get('website', ''),
                    'password': data.get('password', '')
                }
            else:
                return {
                    'email': 0,
                    'name': 0,
                    'code': 0,
                    'website': 0,
                    'password': 0
                }
        except Exception as e:
            return {
                'email': 0,
                'name': 0,
                'code': 0,
                'website': 0,
                'password': 0
            }
    
    def change_user_password(self, email, new_password):
        if len(new_password) > 500:
            return {"success": False, "error": "Password exceeds 500 characters"}
        
        try:
            doc_ref = self.collection.document(email)
            if not doc_ref.get().exists:
                return {"success": False, "error": "User not found"}
            
            doc_ref.update({'password': new_password})
            return {"success": True, "message": f"Password updated for {email}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_user(self, email, **kwargs):
        try:
            doc_ref = self.collection.document(email)
            if not doc_ref.get().exists:
                return {"success": False, "error": "User not found"}
            
            updates = {k: v for k, v in kwargs.items() if v is not None}
            if 'password' in updates and len(updates['password']) > 500:
                return {"success": False, "error": "Password exceeds 500 characters"}
            
            doc_ref.update(updates)
            return {"success": True, "message": f"User {email} updated successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_user(self, email):
        try:
            self.collection.document(email).delete()
            return {"success": True, "message": f"User {email} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_users(self):
        try:
            users = []
            docs = self.collection.stream()
            for doc in docs:
                user_data = doc.to_dict()
                user_data['email'] = doc.id
                users.append(user_data)
            return {"success": True, "data": users}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def user_exists(self, email):
        try:
            doc = self.collection.document(email).get()
            return doc.exists
        except Exception as e:
            return False