import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Layers, Bell, CheckCircle, Clock } from 'lucide-react';

const data = [
  { name: 'Mon', area: 12.5 },
  { name: 'Tue', area: 45.2 },
  { name: 'Wed', area: 32.1 },
  { name: 'Thu', area: 89.4 },
  { name: 'Fri', area: 54.3 },
  { name: 'Sat', area: 22.7 },
  { name: 'Sun', area: 67.8 },
];

const Dashboard = ({ jobs, onJobSelect }) => {
  return (
    <div className="flex flex-col gap-6 h-full p-6 text-white overflow-y-auto">
      {/* Header Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Total Area Analyzed', value: '1.2M km²', icon: Layers, color: 'text-blue-400' },
          { label: 'Changes Detected', value: '1,452', icon: Activity, color: 'text-emerald-400' },
          { label: 'Active Alerts', value: '12', icon: Bell, color: 'text-amber-400' },
        ].map((stat, i) => (
          <div key={i} className="p-4 glass rounded-xl border border-white/5 flex items-center gap-4">
            <div className={`p-2 rounded-lg bg-white/5 ${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-xs text-white/40">{stat.label}</p>
              <p className="text-xl font-bold tracking-tight">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Analytics Chart */}
      <div className="p-6 glass rounded-2xl border border-white/5">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold tracking-tight">Temporal Change Analysis</h2>
          <select className="bg-white/5 border border-white/10 rounded-md text-xs px-2 py-1 outline-none">
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
        </div>
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                    <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                </defs>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#4b5563', fontSize: 12}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#4b5563', fontSize: 12}} />
                <Tooltip 
                    contentStyle={{backgroundColor: '#141417', border: '1px solid #ffffff1a', borderRadius: '8px'}}
                    itemStyle={{color: '#fff'}}
                />
                <Area type="monotone" dataKey="area" stroke="#3b82f6" fillOpacity={1} fill="url(#colorArea)" />
              </AreaChart>
            </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity / Jobs Feed */}
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold tracking-tight">Recent Detection Jobs</h2>
        <div className="flex flex-col gap-2">
            {[
                { id: 1, name: 'Urban Growth - Berlin', date: '2h ago', status: 'completed', changes: 45 },
                { id: 2, name: 'Deforestation Monitor - Amazon Zone 4', date: '5h ago', status: 'processing', changes: null },
                { id: 3, name: 'Post-Flood Assessment - Dhaka', date: '1d ago', status: 'completed', changes: 120 },
            ].map((job) => (
                <div 
                    key={job.id} 
                    className="p-4 glass rounded-xl border border-white/5 flex items-center justify-between hover:bg-white/5 transition-colors cursor-pointer group"
                    onClick={() => onJobSelect(job)}
                >
                    <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-full ${job.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400 animate-pulse'}`}>
                             {job.status === 'completed' ? <CheckCircle size={18} /> : <Clock size={18} />}
                        </div>
                        <div>
                            <p className="text-sm font-medium">{job.name}</p>
                            <p className="text-xs text-white/40">{job.date}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        {job.changes && (
                            <span className="text-xs font-semibold px-2 py-1 bg-red-500/10 text-red-400 rounded-md">
                                {job.changes} Δ Detected
                            </span>
                        )}
                        <svg className="text-white/20 group-hover:text-white/60 transition-colors" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"></path></svg>
                    </div>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
