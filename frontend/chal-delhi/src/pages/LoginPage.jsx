import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import bg2 from "../assets/bg2.MP4";

const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [displayedText, setDisplayedText] = useState('');
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [signupData, setSignupData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');

  // API base URL
  const API_BASE_URL = 'https://cd-back-hnlv.onrender.com/api';

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

  const handleLoginChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!loginData.email || !loginData.password) {
      toast.error('Please fill in all fields!');
      return;
    }

    if (!loginData.email.includes('@')) {
      toast.error('Please enter a valid email address!');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginData.email,
          password: loginData.password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Store user ID in localStorage
        localStorage.setItem('userId', data.user.id.toString());
        // localStorage.setItem('userEmail', data.user.email);
        // localStorage.setItem('userFullName', data.user.fullName);
        
        toast.success('Welcome back! Login successful ');
        console.log('Login data:', data);
        window.location.href = '/chat';
      } else {
        toast.error(data.message || 'Login failed!');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Network error. Please check your connection!');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    if (!signupData.fullName || !signupData.email || !signupData.password || !signupData.confirmPassword) {
      toast.error('Please fill in all fields!');
      return;
    }

    if (!signupData.email.includes('@')) {
      toast.error('Please enter a valid email address!');
      return;
    }

    if (signupData.password.length < 6) {
      toast.error('Password must be at least 6 characters long!');
      return;
    }

    if (signupData.password !== signupData.confirmPassword) {
      toast.error('Passwords do not match!');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fullName: signupData.fullName,
          email: signupData.email,
          password: signupData.password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Store user ID in localStorage
        localStorage.setItem('userId', data.user.id.toString());
        // localStorage.setItem('userEmail', data.user.email);
        // localStorage.setItem('userFullName', data.user.fullName);
        
        toast.success('Account created successfully! Welcome to Chal Dilli ');
        console.log('Signup data:', data);
        window.location.href = '/chat';
        
        // Switch to login after successful signup
        setTimeout(() => {
          setIsLogin(true);
          setSignupData({
            fullName: '',
            email: '',
            password: '',
            confirmPassword: ''
          });
        }, 2000);
      } else {
        toast.error(data.message || 'Signup failed!');
      }
    } catch (error) {
      console.error('Signup error:', error);
      toast.error('Network error. Please check your connection!');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPasswordClick = () => {
    setIsForgotPassword(true);
  };

  const handleSendResetLink = async () => {
    if (!forgotPasswordEmail) {
      toast.info('Please enter your email!');
      return;
    }

    if (!forgotPasswordEmail.includes('@')) {
      toast.error('Please enter a valid email address!');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: forgotPasswordEmail,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Password reset link sent to your email! ');
        setForgotPasswordEmail('');
        setTimeout(() => {
          setIsForgotPassword(false);
        }, 2000);
      } else {
        toast.error(data.message || 'Failed to send reset link!');
      }
    } catch (error) {
      console.error('Forgot password error:', error);
      toast.error('Network error. Please check your connection!');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setIsForgotPassword(false);
    setForgotPasswordEmail('');
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden px-4">

      {/* Background video placeholder */}
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

        {/* Right Side - Login/Signup Card */}
        {/* <div className="w-full max-w-md flex-1"> */}
            <div className="w-full max-w-lg flex-1">
          <div
            className="rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
              backdropFilter: 'blur(10px)',
            }}
          >

            {/* Forms Container */}
            <div className="p-6 md:p-8">
              {isForgotPassword ? (
                /* Forgot Password Form */
                <div className="space-y-6">
                  <div className="text-center space-y-2">
                    <h2 className="text-2xl md:text-3xl font-bold text-amber-100">
                      Reset Password
                    </h2>
                    <p className="text-amber-200/80 text-sm">
                      Enter your email to receive reset link
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={forgotPasswordEmail}
                        onChange={(e) => setForgotPasswordEmail(e.target.value)}
                        placeholder="Enter your email"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                    </div>

                    <button
                      onClick={handleSendResetLink}
                      disabled={loading}
                      className="w-full py-3 bg-black hover:bg-orange-500 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                    >
                      {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>

                    <button
                      type="button"
                      onClick={handleBackToLogin}
                      disabled={loading}
                      className="w-full text-amber-100 hover:text-amber-200 underline underline-offset-2 transition-colors text-sm"
                    >
                      Back to Login
                    </button>
                  </div>
                </div>
              ) : isLogin ? (
                /* Login Form */
                <div className="space-y-6">
                  <div className="text-center space-y-2">
                    <h2 className="text-2xl md:text-3xl font-bold text-amber-100">
                      Welcome Back!
                    </h2>
                    <p className="text-amber-200/80 text-sm">
                      Chal Dilli missed you 💔
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={loginData.email}
                        onChange={handleLoginChange}
                        placeholder="Enter your email"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Password
                      </label>
                      <input
                        type="password"
                        name="password"
                        value={loginData.password}
                        onChange={handleLoginChange}
                        placeholder="Enter your password"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          name="rememberMe"
                          checked={loginData.rememberMe}
                          onChange={handleLoginChange}
                          disabled={loading}
                          className="w-4 h-4 rounded border-amber-700/30 bg-amber-900/40 text-amber-600 focus:ring-2 focus:ring-amber-500/50"
                        />
                        <span className="text-amber-200/90">Remember me</span>
                      </label>
                      <button
                        type="button"
                        onClick={handleForgotPasswordClick}
                        disabled={loading}
                        className="text-amber-200 hover:text-amber-100 underline underline-offset-2 transition-colors"
                      >
                        Forgot Password?
                      </button>
                    </div>

                    <button
                      onClick={handleLogin}
                      disabled={loading}
                      className="w-full py-3 bg-black hover:bg-orange-500 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                    >
                      {loading ? 'Logging in...' : 'Login'}
                    </button>

                    <p className="text-center text-amber-200/80 text-sm">
                      New user?{' '}
                      <button
                        type="button"
                        onClick={() => setIsLogin(false)}
                        disabled={loading}
                        className="text-amber-100 font-semibold hover:underline underline-offset-2"
                      >
                        Sign up
                      </button>
                    </p>
                  </div>
                </div>
              ) : (
                /* Signup Form */
                <div className="space-y-6">
                  <div className="text-center space-y-2">
                    <h2 className="text-2xl md:text-3xl font-bold text-amber-100">
                      Join Chal Dilli!
                    </h2>
                    <p className="text-amber-200/80 text-sm">
                      Your Delhi adventure starts here 🚀
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        name="fullName"
                        value={signupData.fullName}
                        onChange={handleSignupChange}
                        placeholder="Enter your full name"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={signupData.email}
                        onChange={handleSignupChange}
                        placeholder="Enter your email"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                    </div>

                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Password
                      </label>
                      <input
                        type="password"
                        name="password"
                        value={signupData.password}
                        onChange={handleSignupChange}
                        placeholder="Minimum 6 characters"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                      {signupData.password && signupData.password.length < 6 && (
                        <p className="text-red-300 text-xs mt-1">
                          ⚠️ Password must be at least 6 characters
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-amber-100 text-sm font-medium mb-2">
                        Confirm Password
                      </label>
                      <input
                        type="password"
                        name="confirmPassword"
                        value={signupData.confirmPassword}
                        onChange={handleSignupChange}
                        placeholder="Re-enter your password"
                        disabled={loading}
                        className="w-full px-4 py-3 rounded-lg bg-amber-900/40 border border-amber-700/30 text-amber-100 placeholder-amber-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all"
                      />
                      {signupData.confirmPassword && signupData.password !== signupData.confirmPassword && (
                        <p className="text-red-300 text-xs mt-1">
                          ⚠️ Passwords do not match
                        </p>
                      )}
                      {signupData.confirmPassword && signupData.password === signupData.confirmPassword && signupData.password.length >= 6 && (
                        <p className="text-green-300 text-xs mt-1">
                          ✓ Passwords match
                        </p>
                      )}
                    </div>

                    <button
                      onClick={handleSignup}
                      disabled={loading}
                      className="w-full py-3 bg-black hover:bg-orange-500 text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                    >
                      {loading ? 'Creating account...' : 'Sign Up'}
                    </button>

                    <p className="text-center text-amber-200/80 text-sm">
                      Already have an account?{' '}
                      <button
                        type="button"
                        onClick={() => setIsLogin(true)}
                        disabled={loading}
                        className="text-amber-100 font-semibold hover:underline underline-offset-2"
                      >
                        Login
                      </button>
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
