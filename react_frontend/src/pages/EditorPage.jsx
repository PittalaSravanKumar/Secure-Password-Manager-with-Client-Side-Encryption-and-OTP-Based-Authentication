import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useNotes } from '../hooks/useNotes';

export default function EditorPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { notes, saveNote, deleteNote } = useNotes();
  
  const isNew = id === 'new';
  const existingNote = !isNew ? notes.find(n => n.id === id) : null;

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(isNew ? 'Unsaved' : 'Saved');

  // Debounce saving timer
  const saveTimeoutRef = useRef(null);

  // Load existing note data
  useEffect(() => {
    if (existingNote) {
      setTitle(existingNote.title || '');
      setContent(existingNote.content || '');
    }
  }, [existingNote]);

  // Auto-save logic
  useEffect(() => {
    if (title === '' && content === '') return;
    
    // Skip initial load auto-save if data matches
    if (existingNote && title === existingNote.title && content === existingNote.content) {
      setSaveStatus('Saved');
      return;
    }

    setSaveStatus('Saving...');
    
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        setIsSaving(true);
        const newId = await saveNote(id, title, content);
        setSaveStatus('Saved Securely');
        
        // Update URL if it was a new note that just got an ID
        if (isNew && newId) {
          navigate(`/note/${newId}`, { replace: true });
        }
      } catch (error) {
        console.error('Save failed:', error);
        setSaveStatus('Error saving');
      } finally {
        setIsSaving(false);
      }
    }, 1000); // 1 second debounce

    return () => clearTimeout(saveTimeoutRef.current);
  }, [title, content, id, isNew, navigate, saveNote, existingNote]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this secure note?')) {
      try {
        await deleteNote(id);
        navigate('/');
      } catch (error) {
        console.error('Delete failed:', error);
        alert('Could not delete note');
      }
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Editor Header */}
      <header className="sticky top-0 bg-white border-b border-gray-100 px-4 py-3 flex justify-between items-center z-10">
        <button 
          onClick={() => navigate('/')}
          className="text-gray-500 hover:text-gray-800 flex items-center transition-colors focus:outline-none"
        >
          <span className="mr-2">←</span> Back
        </button>
        
        <div className={`text-sm flex items-center transition-colors ${saveStatus === 'Error saving' ? 'text-red-500' : 'text-gray-400'}`}>
          {saveStatus === 'Saved Securely' && (
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
          )}
          {saveStatus === 'Saving...' && (
            <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {saveStatus}
        </div>
        
        <div className="flex gap-2">
          {!isNew && (
            <button 
              onClick={handleDelete}
              title="Delete Note"
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors focus:outline-none"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </header>

      {/* Editor Body */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-8 flex flex-col">
        <input 
          type="text" 
          placeholder="Note Title" 
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="text-4xl font-bold text-gray-900 border-none outline-none focus:ring-0 mb-6 bg-transparent placeholder-gray-300"
        />
        
        <textarea 
          placeholder="Write your secure note here..." 
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="flex-1 w-full resize-none text-lg text-gray-800 border-none outline-none focus:ring-0 bg-transparent placeholder-gray-300 leading-relaxed"
        />
      </main>
    </div>
  );
}
