import { useState, useEffect } from 'react';
import { Note } from '../types';

interface NoteEditorProps {
    note: Note;
    onUpdate: (id: string, updates: Partial<Note>) => void;
}

export function NoteEditor({ note, onUpdate }: NoteEditorProps) {
    const [title, setTitle] = useState(note.title);
    const [content, setContent] = useState(note.content);

    // Update local state when note changes (e.g. selection change)
    useEffect(() => {
        setTitle(note.title);
        setContent(note.content);
    }, [note.id]);

    // Debounced save
    useEffect(() => {
        const timer = setTimeout(() => {
            if (title !== note.title || content !== note.content) {
                onUpdate(note.id, { title, content });
            }
        }, 1000);

        return () => clearTimeout(timer);
    }, [title, content, note.id, note.title, note.content, onUpdate]);

    return (
        <div className="flex flex-col h-full bg-[#0a0a0a]">
            <div className="p-8 pb-6 border-b border-[#262626] bg-[#111111]/50">
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Note Title"
                    className="w-full bg-transparent text-4xl font-bold text-[#f5f5f5] focus:outline-none placeholder-[#737373] tracking-tight"
                />
                <div className="mt-4 flex items-center space-x-4 text-xs text-[#737373]">
                    <span>Last edited {new Date(note.updated_at).toLocaleString()}</span>
                </div>
            </div>
            <div className="flex-1 p-8 pt-6 overflow-auto">
                <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Start writing..."
                    className="w-full h-full min-h-full bg-transparent text-[#a3a3a3] resize-none focus:outline-none font-sans text-base leading-relaxed placeholder-[#737373]"
                    spellCheck={false}
                />
            </div>
        </div>
    );
}
