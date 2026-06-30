// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBUgh7vPMwcReH3Ymq62czUDe6f-VFY2CA",
  authDomain: "password-manager-system-2b723.firebaseapp.com",
  projectId: "password-manager-system-2b723",
  storageBucket: "password-manager-system-2b723.firebasestorage.app",
  messagingSenderId: "431650424075",
  appId: "1:431650424075:web:566c2afdaa2292c3204e0e",
  measurementId: "G-7XFPZLE6DR"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const analytics = getAnalytics(app);
