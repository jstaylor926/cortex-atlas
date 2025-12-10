import { Note } from '../types';
import { FileText, Plus } from 'lucide-react';

interface NotesListProps {
    notes: Note[];
    selectedNoteId: string | null;
    onSelectNote: (note: Note) => void;
    onCreateNote: () => void;
}

export function NotesList({ notes, selectedNoteId, onSelectNote, onCreateNote }: NotesListProps) {
    return (
        <div className="w-80 bg-[#111111] border-r border-[#262626] flex flex-col h-full">
            <div className="p-4 border-b border-[#262626] flex justify-between items-center bg-[#0a0a0a]/50">
                <h2 className="font-semibold text-[#f5f5f5] tracking-wide text-sm uppercase">Notes</h2>
                <button
                    onClick={onCreateNote}
                    className="p-2 hover:bg-[#1a1a1a] rounded-lg text-[#737373] hover:text-blue-400 transition-all duration-200 hover:border border-[#262626]"
                    title="New Note"
                >
                    <Plus size={18} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {notes.length === 0 ? (
                    <div className="p-8 text-center text-[#737373] text-sm">
                        <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-[#151515] border border-[#262626] flex items-center justify-center">
                            <FileText size={20} className="text-[#737373]" />
                        </div>
                        <p>No notes yet.</p>
                        <p className="mt-1">Create one to get started.</p>
                    </div>
                ) : (
                    <div className="p-2 space-y-1">
                        {notes.map((note) => {
                            const isSelected = selectedNoteId === note.id;
                            return (
                                <button
                                    key={note.id}
                                    onClick={() => onSelectNote(note)}
                                    className={`w-full text-left p-3 rounded-lg transition-all duration-200 group ${
                                        isSelected
                                            ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                                            : 'hover:bg-[#1a1a1a] border border-transparent hover:border-[#262626]'
                                    }`}
                                >
                                    <div className={`font-medium truncate transition-colors mb-1 ${
                                        isSelected ? 'text-[#f5f5f5]' : 'text-[#a3a3a3] group-hover:text-[#f5f5f5]'
                                    }`}>
                                        {note.title || 'Untitled Note'}
                                    </div>
                                    <div className="text-xs text-[#737373] flex items-center justify-between">
                                        <span className="flex items-center">
                                            <FileText size={10} className="mr-1.5" />
                                            {new Date(note.updated_at).toLocaleDateString(undefined, { 
                                                month: 'short', 
                                                day: 'numeric',
                                                year: new Date(note.updated_at).getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
                                            })}
                                        </span>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
