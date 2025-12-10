import { LayoutDashboard, FileText, CheckSquare, Calendar, TrendingUp, Clock } from 'lucide-react';

export function Dashboard() {
    const stats = [
        { label: 'Total Notes', value: '24', icon: FileText, color: 'blue', change: '+3' },
        { label: 'Active Tasks', value: '12', icon: CheckSquare, color: 'green', change: '+2' },
        { label: 'Upcoming Events', value: '5', icon: Calendar, color: 'purple', change: '0' },
        { label: 'This Week', value: '18', icon: TrendingUp, color: 'orange', change: '+8%' },
    ];

    const recentActivity = [
        { type: 'note', title: 'Project Planning', time: '2 hours ago', icon: FileText },
        { type: 'task', title: 'Review API design', time: '4 hours ago', icon: CheckSquare },
        { type: 'note', title: 'Meeting notes', time: '1 day ago', icon: FileText },
        { type: 'event', title: 'Team standup', time: '2 days ago', icon: Calendar },
    ];

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6 bg-[#0a0a0a]">
            {/* Welcome Section */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-[#f5f5f5] mb-2">Welcome back</h1>
                <p className="text-[#a3a3a3]">Here's what's happening with your workspace today</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    const colorClasses = {
                        blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30 text-blue-400',
                        green: 'from-green-500/20 to-green-600/20 border-green-500/30 text-green-400',
                        purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30 text-purple-400',
                        orange: 'from-orange-500/20 to-orange-600/20 border-orange-500/30 text-orange-400',
                    };

                    return (
                        <div
                            key={stat.label}
                            className="bg-[#151515] border border-[#262626] rounded-xl p-5 hover:border-[#2a2a2a] transition-all duration-200 group hover:shadow-lg hover:shadow-black/20"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className={`p-2.5 rounded-lg bg-gradient-to-br ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                                    <Icon size={20} />
                                </div>
                                <span className={`text-xs font-medium px-2 py-1 rounded-md bg-[#1a1a1a] text-[#a3a3a3]`}>
                                    {stat.change}
                                </span>
                            </div>
                            <div className="space-y-1">
                                <p className="text-2xl font-bold text-[#f5f5f5]">{stat.value}</p>
                                <p className="text-sm text-[#a3a3a3]">{stat.label}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Today's Focus */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Quick Actions */}
                    <div className="bg-[#151515] border border-[#262626] rounded-xl p-6">
                        <h2 className="text-lg font-semibold text-[#f5f5f5] mb-4 flex items-center">
                            <Clock size={20} className="mr-2 text-blue-400" />
                            Today's Focus
                        </h2>
                        <div className="space-y-3">
                            <div className="p-4 bg-[#1a1a1a] rounded-lg border border-[#262626] hover:border-blue-500/30 transition-all cursor-pointer group">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <p className="text-[#f5f5f5] font-medium group-hover:text-blue-400 transition-colors">
                                            Complete API documentation
                                        </p>
                                        <p className="text-sm text-[#737373] mt-1">Due in 3 hours</p>
                                    </div>
                                    <div className="w-2 h-2 rounded-full bg-green-400 ml-3 mt-1.5"></div>
                                </div>
                            </div>
                            <div className="p-4 bg-[#1a1a1a] rounded-lg border border-[#262626] hover:border-purple-500/30 transition-all cursor-pointer group">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <p className="text-[#f5f5f5] font-medium group-hover:text-purple-400 transition-colors">
                                            Review pull requests
                                        </p>
                                        <p className="text-sm text-[#737373] mt-1">Due tomorrow</p>
                                    </div>
                                    <div className="w-2 h-2 rounded-full bg-purple-400 ml-3 mt-1.5"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Recent Notes */}
                    <div className="bg-[#151515] border border-[#262626] rounded-xl p-6">
                        <h2 className="text-lg font-semibold text-[#f5f5f5] mb-4 flex items-center">
                            <FileText size={20} className="mr-2 text-blue-400" />
                            Recent Notes
                        </h2>
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <div
                                    key={i}
                                    className="p-4 bg-[#1a1a1a] rounded-lg border border-[#262626] hover:border-blue-500/30 transition-all cursor-pointer group"
                                >
                                    <p className="text-[#f5f5f5] font-medium group-hover:text-blue-400 transition-colors">
                                        Project Planning Document
                                    </p>
                                    <p className="text-sm text-[#737373] mt-1 line-clamp-2">
                                        Updated with new requirements and timeline estimates...
                                    </p>
                                    <p className="text-xs text-[#737373] mt-2">2 hours ago</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Recent Activity */}
                    <div className="bg-[#151515] border border-[#262626] rounded-xl p-6">
                        <h2 className="text-lg font-semibold text-[#f5f5f5] mb-4">Recent Activity</h2>
                        <div className="space-y-4">
                            {recentActivity.map((activity, idx) => {
                                const Icon = activity.icon;
                                return (
                                    <div key={idx} className="flex items-start space-x-3 group">
                                        <div className="p-2 bg-[#1a1a1a] rounded-lg border border-[#262626] group-hover:border-blue-500/30 transition-all">
                                            <Icon size={16} className="text-[#737373] group-hover:text-blue-400 transition-colors" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-[#f5f5f5] font-medium truncate group-hover:text-blue-400 transition-colors">
                                                {activity.title}
                                            </p>
                                            <p className="text-xs text-[#737373] mt-0.5">{activity.time}</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
                        <h2 className="text-lg font-semibold text-[#f5f5f5] mb-4">This Week</h2>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#a3a3a3]">Notes Created</span>
                                <span className="text-lg font-bold text-blue-400">8</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#a3a3a3]">Tasks Completed</span>
                                <span className="text-lg font-bold text-green-400">15</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#a3a3a3]">Events Scheduled</span>
                                <span className="text-lg font-bold text-purple-400">12</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

