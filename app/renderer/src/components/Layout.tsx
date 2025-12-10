import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, CheckSquare, Settings, Terminal, Calendar, Search } from 'lucide-react';

export function Layout() {
    const location = useLocation();

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/notes', icon: FileText, label: 'Notes' },
        { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
        { path: '/calendar', icon: Calendar, label: 'Calendar' },
        { path: '/terminal', icon: Terminal, label: 'Terminal' },
        { path: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="flex h-screen bg-[#0a0a0a] text-[#f5f5f5] font-sans antialiased">
            {/* Sidebar */}
            <aside className="w-64 bg-[#111111] border-r border-[#262626] flex flex-col shadow-2xl z-10">
                <div className="p-6 border-b border-[#262626]">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
                        Cortex Atlas
                    </h1>
                    <p className="text-xs text-[#737373] mt-1">Local-first personal OS</p>
                </div>

                <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path || 
                            (item.path !== '/' && location.pathname.startsWith(item.path));

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all duration-200 group relative ${
                                    isActive
                                        ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 font-medium shadow-lg shadow-blue-500/10'
                                        : 'text-[#a3a3a3] hover:bg-[#1a1a1a] hover:text-[#f5f5f5]'
                                }`}
                            >
                                {isActive && (
                                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-blue-400 to-purple-400 rounded-r-full" />
                                )}
                                <Icon size={20} className={`transition-colors ${isActive ? 'text-blue-400' : 'text-[#737373] group-hover:text-[#a3a3a3]'}`} />
                                <span className="text-sm">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-[#262626] bg-[#0a0a0a]/50">
                    <div className="text-xs font-medium text-[#737373] text-center">v1.0.0-alpha</div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Top Bar */}
                <header className="h-14 bg-[#111111] border-b border-[#262626] flex items-center px-6 shadow-sm">
                    <div className="flex-1 flex items-center space-x-4">
                        <div className="relative flex-1 max-w-md">
                            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                            <input
                                type="text"
                                placeholder="Search notes, tasks, events..."
                                className="w-full pl-10 pr-4 py-2 bg-[#1a1a1a] border border-[#262626] rounded-lg text-sm text-[#f5f5f5] placeholder-[#737373] focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                            />
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 flex items-center justify-center text-white text-xs font-semibold">
                            A
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="flex-1 overflow-hidden relative bg-[#0a0a0a]">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
