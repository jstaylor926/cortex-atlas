import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/apiClient';
import { Note } from '../types';
import { NotesList } from '../components/NotesList';
import { NoteEditor } from '../components/NoteEditor';

export function Notes() {
    const [notes, setNotes] = useState<Note[]>([]);
    const [selectedNote, setSelectedNote] = useState<Note | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchNotes = useCallback(async () => {
        try {
            const response = await api.getNotes();
            // @ts-ignore - API response type needs to be properly typed
            setNotes(response.notes || []);
        } catch (error) {
            console.error('Failed to fetch notes:', error);
            // Show user-friendly error message
            if (error instanceof Error) {
                alert(`Error loading notes: ${error.message}`);
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchNotes();
    }, [fetchNotes]);

    const handleCreateNote = async () => {
        try {
            const newNote = await api.createNote({
                title: 'Untitled Note',
                content: '',
                tags: []
            });
            // @ts-ignore
            setNotes(prev => [newNote, ...prev]);
            // @ts-ignore
            setSelectedNote(newNote);
        } catch (error) {
            console.error('Failed to create note:', error);
        }
    };

    const handleUpdateNote = async (id: string, updates: Partial<Note>) => {
        try {
            // Optimistic update
            setNotes(prev => prev.map(n =>
                n.id === id ? { ...n, ...updates, updated_at: new Date().toISOString() } : n
            ));

            if (selectedNote?.id === id) {
                setSelectedNote(prev => prev ? { ...prev, ...updates } : null);
            }

            await api.updateNote(id, updates);
        } catch (error) {
            console.error('Failed to update note:', error);
            // Revert on error would go here
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center space-y-4">
                    <div className="w-12 h-12 mx-auto rounded-xl bg-[#151515] border border-[#262626] flex items-center justify-center animate-pulse">
                        <svg className="w-6 h-6 text-[#737373]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </div>
                    <p className="text-[#a3a3a3]">Loading notes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-full overflow-hidden bg-[#0a0a0a]">
            <NotesList
                notes={notes}
                selectedNoteId={selectedNote?.id || null}
                onSelectNote={setSelectedNote}
                onCreateNote={handleCreateNote}
            />

            <div className="flex-1 h-full overflow-hidden">
                {selectedNote ? (
                    <NoteEditor
                        note={selectedNote}
                        onUpdate={handleUpdateNote}
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-[#737373] space-y-4">
                        <div className="w-20 h-20 rounded-2xl bg-[#151515] border border-[#262626] flex items-center justify-center">
                            <svg className="w-10 h-10 text-[#737373]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                        </div>
                        <p className="text-lg font-medium text-[#a3a3a3]">Select a note or create a new one</p>
                        <p className="text-sm text-[#737373]">Click the + button to get started</p>
                    </div>
                )}
            </div>
        </div>
    );
}
