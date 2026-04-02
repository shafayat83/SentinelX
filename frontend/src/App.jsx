import React, { useState } from 'react';
import MapView from './components/MapView';
import Dashboard from './components/Dashboard';
import { Home, Map, Layers, Settings, Globe, LogOut, Search, PlusCircle } from 'lucide-react';

const App = () => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [jobs, setJobs] = useState([]);
    const [selectedJob, setSelectedJob] = useState(null);

    const handleJobSelect = (job) => {
        setSelectedJob(job);
        setActiveTab('map');
    };

    return (
        <div className="flex h-screen w-full bg-[#030303] text-white">
            {/* Left Sidebar */}
            <aside className="w-20 lg:w-64 border-r border-white/5 flex flex-col items-center lg:items-start p-6 bg-[#030303] transition-all duration-300">
                <div className="flex items-center gap-3 mb-12">
                    <div className="p-2 bg-blue-600 rounded-lg shadow-lg shadow-blue-600/30">
                        <Globe size={24} className="text-white" />
                    </div>
                    <span className="hidden lg:block text-lg font-bold tracking-tight">MakeIt <span className="text-blue-500">v2.1</span></span>
                </div>

                <nav className="flex flex-col gap-2 w-full flex-grow">
                    <SidebarItem 
                        icon={Home} 
                        label="Dashboard" 
                        active={activeTab === 'dashboard'} 
                        onClick={() => setActiveTab('dashboard')} 
                    />
                    <SidebarItem 
                        icon={Map} 
                        label="Live Map" 
                        active={activeTab === 'map'} 
                        onClick={() => setActiveTab('map')} 
                    />
                    <SidebarItem 
                        icon={Layers} 
                        label="Datasets" 
                    />
                    <SidebarItem 
                        icon={Settings} 
                        label="Settings" 
                    />
                </nav>

                <button className="flex items-center gap-3 p-3 w-full rounded-xl text-white/40 hover:bg-white/5 hover:text-white transition-all group">
                    <LogOut size={20} />
                    <span className="hidden lg:block text-sm font-medium">Log out</span>
                </button>
            </aside>

            {/* Main Content Area */}
            <main className="flex-grow flex flex-col relative overflow-hidden">
                {/* Header Navbar */}
                <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-[#030303]/80 backdrop-blur-md z-10">
                    <div className="flex items-center gap-4 bg-white/5 border border-white/10 px-4 py-2 rounded-full w-full max-w-lg">
                        <Search size={18} className="text-white/40" />
                        <input 
                            placeholder="Find target coordinates (e.g. 31.25, 34.88)..." 
                            className="bg-transparent border-none outline-none text-sm text-white flex-grow"
                        />
                    </div>
                    
                    <div className="flex items-center gap-4">
                         <button className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-full text-sm font-semibold transition-all shadow-lg shadow-blue-600/20 active:scale-95">
                             <PlusCircle size={18} />
                             New Detection Job
                         </button>
                         <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 p-[2px] cursor-pointer">
                            <div className="w-full h-full rounded-full border-2 border-background flex items-center justify-center overflow-hidden">
                                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
                            </div>
                         </div>
                    </div>
                </header>

                <div className="flex-grow relative h-0">
                    {activeTab === 'dashboard' ? (
                        <Dashboard jobs={jobs} onJobSelect={handleJobSelect} />
                    ) : (
                        <MapView resultGeoJSON={selectedJob?.result_geojson} />
                    )}
                </div>
            </main>
        </div>
    );
};

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <div 
        onClick={onClick}
        className={`flex items-center gap-3 p-4 w-full rounded-xl cursor-pointer transition-all duration-300 group
        ${active ? 'bg-blue-600/10 text-blue-500' : 'text-white/40 hover:bg-white/5 hover:text-white'}`}
    >
        <div className={`transition-transform duration-300 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>
            <Icon size={20} />
        </div>
        <span className={`hidden lg:block text-sm font-medium ${active ? 'font-semibold' : ''}`}>{label}</span>
        {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_#3b82f6]" />}
    </div>
);

export default App;
