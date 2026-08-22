import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import bg2 from "../assets/bg2.MP4";
import { AUTH_API_URL, AUTH_ENABLED } from "../config";

const ResetPasswordPage = () => {
  const [loading, setLoading] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [resetData, setResetData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  const [urlParams, setUrlParams] = useState({
    token: '',
    userId: ''  
  });

  // API base URL
  const API_BASE_URL = `${AUTH_API_URL}/api`;

  // Extract token and id from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const id = params.get('id');
    
    if (!token || !id) {
      toast.error('Invalid reset link!');
    } else {
      setUrlParams({ token, userId: id });
    }
  }, []);

  // Typing animation for "Chal Dilli"
  useEffect(() => {
    const text = 'Chal Dilli';
    let index = 0;
    setDisplayedText('');
    
    const timer = setInterval(() => {
      if (index <= text.length) {
        setDisplayedText(text.slice(0, index));
        index++;
      } else {
        setTimeout(() => {
          index = 0;
          setDisplayedText('');
        }, 2000);
      }
    }, 150);

    return () => clearInterval(timer);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setResetData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (!resetData.newPassword || !resetData.confirmPassword) {
      toast.error('Please fill in all fields!');
      return;
    }

    if (resetData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters long!');
      return;
    }

    if (resetData.newPassword !== resetData.confirmPassword) {
      toast.error('Passwords do not match!');
      return;
    }

    if (!urlParams.token || !urlParams.userId) {
      toast.error('Invalid reset link!');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: urlParams.userId,
          token: urlParams.token,
          newPassword: resetData.newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Password has been reset successfully! 🎉');
        console.log('Reset password response:', data);
        
        // Redirect to login page after 2 seconds
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        toast.error(data.message || 'Failed to reset password!');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      toast.error('Network error. Please check your connection!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden px-4">
      {/* Background - You can replace this with your bg2.mp4 video */}
      <video
  src={bg2}
  autoPlay
  loop
  muted
  playsInline
  className="absolute top-0 left-0 w-full h-full object-cover -z-10"
/>

      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />

      {/* Ambient dots */}
      <div className="absolute inset-0 z-5 pointer-events-none">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-amber-400/30 rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${3 + Math.random() * 2}s`,
            }}
          />
        ))}
      </div>

      {/* Main Container - Side by Side Layout */}
      <div className="relative z-10 w-full max-w-6xl flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16">
        
        {/* Left Side - Chal Dilli Branding */}
        <div className="text-left md:text-left flex-1">
          <h1 className="text-6xl md:text-8xl font-bold text-white mb-4 min-h-[120px]">
            {displayedText}<span className="animate-pulse">|</span>
          </h1>
          <p className="text-white text-xl md:text-2xl font-semibold">
            DILWALE SE PUCHO DILLI KA RASTA
          </p>
        </div>

        {/* Right Side - Reset Password Card */}
        <div className="w-full max-w-lg flex-1">
          <div
            className="rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
              backdropFilter: 'blur(10px)',
            }}
          >
            {/* Form Container */}
            <div className="p-6 md:p-8">
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl md:text-3xl font-bold text-amber-100">
                    Reset Your Password
                  </h2>
                  <p className="text-amber-200/80 text-sm">
                    Enter your new password below 🔐
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-amber-100 text-sm font-medium mb-2">
                      New Password
                    </label>
                    <input
                      type="password"
                      name="newPassword"
                      value={resetData.newPassword}
                      onChange={handleChange}
                      placeholder="Minimum 6 characters"
                      disabled={loading}
                      className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                    />
                    {resetData.newPassword && resetData.newPassword.length < 6 && (
                      <p className="text-red-300 text-xs mt-1">
                        ⚠️ Password must be at least 6 characters
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-amber-100 text-sm font-medium mb-2">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={resetData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Re-enter your password"
                      disabled={loading}
                      className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                    />
                    {resetData.confirmPassword && resetData.newPassword !== resetData.confirmPassword && (
                      <p className="text-red-300 text-xs mt-1">
                        ⚠️ Passwords do not match
                      </p>
                    )}
                    {resetData.confirmPassword && resetData.newPassword === resetData.confirmPassword && resetData.newPassword.length >= 6 && (
                      <p className="text-green-300 text-xs mt-1">
                        ✓ Passwords match
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handleResetPassword}
                    disabled={loading}
                    className="w-full py-3 bg-black hover:bg-orange-500 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                  >
                    {loading ? 'Resetting...' : 'Reset Password'}
                  </button>

                  <div className="text-center">
                    <a
                      href="/"
                      className="text-amber-200 hover:text-amber-100 underline underline-offset-2 transition-colors text-sm"
                    >
                      Back to Login
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
