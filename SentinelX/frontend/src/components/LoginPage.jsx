import React, { useState } from 'react';
import { login } from '../api/client';
import { Lock, User, AlertCircle, Shield } from 'lucide-react';

const LoginPage = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);
        
        if (!username || !password) {
            setError("Please fill in both fields");
            return;
        }

        setLoading(true);
        try {
            await login(username, password);
            onLoginSuccess();
        } catch (err) {
            setError(err.message || "Failed to login. Check credentials.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen w-full bg-[#030303] text-white items-center justify-center">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5" />
            
            <div className="z-10 w-full max-w-md p-8 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl shadow-2xl">
                <div className="flex justify-center mb-8">
                    <div className="p-3 bg-blue-600 rounded-xl shadow-lg shadow-blue-600/30">
                        <Shield size={32} className="text-white" />
                    </div>
                </div>
                
                <h2 className="text-3xl font-bold tracking-tight text-center mb-2">SentinelX</h2>
                <p className="text-white/50 text-center mb-8">Secure Access Portal</p>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-500">
                        <AlertCircle size={20} />
                        <span className="text-sm font-medium">{error}</span>
                    </div>
                )}

                <form onSubmit={handleLogin} className="space-y-5">
                    <div className="space-y-2">
                        <label className="text-xs font-semibold text-white/50 uppercase tracking-wider">Username</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <User size={18} className="text-white/30" />
                            </div>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder-white/20 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                                placeholder="analyst_admin"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-semibold text-white/50 uppercase tracking-wider">Password</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Lock size={18} className="text-white/30" />
                            </div>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder-white/20 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full py-3.5 mt-4 rounded-xl font-bold tracking-wide transition-all ${
                            loading ? "bg-blue-600/50 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-500 active:scale-[0.98] shadow-lg shadow-blue-600/20"
                        }`}
                    >
                        {loading ? "Authenticating..." : "Login"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LoginPage;
