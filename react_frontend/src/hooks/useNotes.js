import { useState, useEffect } from 'react';
import { 
  collection, 
  query, 
  where, 
  orderBy, 
  onSnapshot,
  doc,
  setDoc,
  addDoc,
  deleteDoc,
  serverTimestamp
} from 'firebase/firestore';
import { db } from '../config/firebase';
import { useAuth } from '../context/AuthContext';
import { encryptText, decryptText } from '../services/crypto';

export function useNotes() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const { currentUser } = useAuth();

  useEffect(() => {
    if (!currentUser) {
      setNotes([]);
      setLoading(false);
      return;
    }

    const q = query(
      collection(db, 'notes'),
      where('userId', '==', currentUser.uid),
      orderBy('updatedAt', 'desc')
    );

    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const notesData = querySnapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          // Decrypt title and content on read
          title: decryptText(data.title),
          content: decryptText(data.content),
        };
      });
      setNotes(notesData);
      setLoading(false);
    }, (error) => {
      console.error("Error fetching notes:", error);
      setLoading(false);
    });

    return unsubscribe;
  }, [currentUser]);

  const saveNote = async (id, title, content) => {
    if (!currentUser) throw new Error('Must be logged in to save notes');

    // Encrypt fields before saving
    const encryptedTitle = encryptText(title);
    const encryptedContent = encryptText(content);

    const noteData = {
      userId: currentUser.uid,
      title: encryptedTitle,
      content: encryptedContent,
      updatedAt: serverTimestamp()
    };

    if (id && id !== 'new') {
      // Update existing
      const noteRef = doc(db, 'notes', id);
      await setDoc(noteRef, noteData, { merge: true });
      return id;
    } else {
      // Add new
      const docRef = await addDoc(collection(db, 'notes'), {
        ...noteData,
        createdAt: serverTimestamp()
      });
      return docRef.id;
    }
  };

  const deleteNote = async (id) => {
    if (!currentUser || !id || id === 'new') return;
    await deleteDoc(doc(db, 'notes', id));
  };

  return { notes, loading, saveNote, deleteNote };
}
