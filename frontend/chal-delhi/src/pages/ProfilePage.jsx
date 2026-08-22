import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import bg2 from "../assets/bg2.MP4";
import { AUTH_API_URL, AUTH_ENABLED } from "../config";

const ProfilePage = () => {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  
  // Sample user data - plan/stats kept as is, only name/email will be updated from API
  const [userData, setUserData] = useState({
    fullName: 'Krish Batra',
    email: 'krish@chaldilli.com',
    joinDate: 'January 15, 2024',
    plan: {
      name: 'Premium',
      type: 'Monthly',
      price: '₹299',
      features: [
        'Unlimited event searches',
        'Priority recommendations',
        'Advanced filters',
        'Ad-free experience',
        '24/7 Support'
      ],
      expiryDate: 'December 22, 2025',
      status: 'Active'
    },
    stats: {
      queriesAsked: 152,
      eventsExplored: 48,
      favoriteSpots: 23
    }
  });

  // 🔹 Fetch name & email from API using userId1 from localStorage
  useEffect(() => {
    const fetchUserDetails = async () => {
      try {
        const userId = localStorage.getItem('userId');
        if (!userId) {
          toast.error('User not found. Please login again.');
          return;
        }

        const res = await fetch(`${AUTH_API_URL}/api/users/${userId}`);
        if (!res.ok) {
          throw new Error('Failed to fetch user details');
        }

        const data = await res.json();
        if (data && data.user) {
          setUserData((prev) => ({
            ...prev,
            fullName: data.user.full_name,
            email: data.user.email,
          }));
        }
      } catch (error) {
        console.error('Error fetching user details:', error);
        toast.error('Failed to load user details');
      }
    };

    fetchUserDetails();
  }, []);

  const handleLogout = () => {
    toast.info('Logging out...');
    setTimeout(() => {
      // 🔹 Clear local storage & redirect to "/"
      localStorage.clear();
      window.location.href = '/';
    }, 1000);
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText.toLowerCase() !== 'delete') {
      toast.error('Please type DELETE to confirm');
      return;
    }

    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        toast.error('User not found. Please login again.');
        return;
      }

      const res = await fetch(`${AUTH_API_URL}/api/users/${userId}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        throw new Error('Failed to delete account');
      }

      toast.success('Account deleted successfully. Redirecting...');
      setShowDeleteModal(false);
      setDeleteConfirmText('');

      setTimeout(() => {
        // 🔹 Clear local storage & redirect after deletion
        localStorage.clear();
        window.location.href = '/';
      }, 1500);
    } catch (error) {
      console.error('Error deleting account:', error);
      toast.error('Failed to delete account. Please try again.');
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden">

  {/* Background Video */}
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

      {/* Header */}
      <div className="absolute top-4 md:top-8 left-1/2 transform -translate-x-1/2 z-30 px-4 text-center">
        <h1 className="text-4xl md:text-7xl font-bold text-black mb-1 md:mb-2">
          Chal Dilli
        </h1>
        <p className="text-black text-center text-base md:text-lg font-semibold">
          The only sathi for a Dilli vasi !!
        </p>
      </div>

      {/* Profile Content */}
      <div className="absolute top-28 md:top-36 bottom-8 left-4 right-4 md:left-8 md:right-8 z-20 overflow-y-auto">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Profile Header Card */}
          <div
            className="rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div className="p-6 md:p-8">
              <div className="flex flex-col md:flex-row items-center md:items-start space-y-4 md:space-y-0 md:space-x-6">
                {/* Avatar */}
                <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-white font-bold text-4xl md:text-5xl shadow-xl flex-shrink-0">
                  {userData.fullName.charAt(0)}
                </div>
                
                {/* User Info */}
                <div className="flex-1 text-center md:text-left">
                  <h2 className="text-2xl md:text-3xl font-bold text-amber-100 mb-2">
                    {userData.fullName}
                  </h2>
                  <p className="text-amber-200/90 text-sm md:text-base mb-1">
                    {userData.email}
                  </p>
                  <p className="text-amber-200/70 text-xs md:text-sm">
                    Member since {userData.joinDate}
                  </p>
                  
                  {/* Stats */}
                  <div className="flex flex-wrap justify-center md:justify-start gap-4 mt-4">
                    <div className="bg-amber-900/40 rounded-lg px-4 py-2 border border-amber-700/30">
                      <p className="text-amber-100 font-semibold text-lg">{userData.stats.queriesAsked}</p>
                      <p className="text-amber-200/80 text-xs">Queries Asked</p>
                    </div>
                    <div className="bg-amber-900/40 rounded-lg px-4 py-2 border border-amber-700/30">
                      <p className="text-amber-100 font-semibold text-lg">{userData.stats.eventsExplored}</p>
                      <p className="text-amber-200/80 text-xs">Events Explored</p>
                    </div>
                    <div className="bg-amber-900/40 rounded-lg px-4 py-2 border border-amber-700/30">
                      <p className="text-amber-100 font-semibold text-lg">{userData.stats.favoriteSpots}</p>
                      <p className="text-amber-200/80 text-xs">Favorite Spots</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Plan Details Card */}
          <div
            className="rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div className="p-6 md:p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl md:text-2xl font-bold text-amber-100">
                  Current Plan
                </h3>
                <span className={`px-4 py-1.5 rounded-full text-xs font-semibold ${
                  userData.plan.status === 'Active' 
                    ? 'bg-green-600/80 text-white' 
                    : 'bg-red-600/80 text-white'
                }`}>
                  {userData.plan.status}
                </span>
              </div>

              <div className="space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div>
                    <h4 className="text-2xl font-bold text-amber-100 mb-1">
                      {userData.plan.name} Plan
                    </h4>
                    <p className="text-amber-200/80 text-sm">
                      {userData.plan.type} • {userData.plan.price}
                    </p>
                  </div>
                  <button className="mt-4 md:mt-0 bg-orange-600/90 hover:bg-orange-500 text-white font-semibold px-6 py-2 rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]">
                    Upgrade Plan
                  </button>
                </div>

                <div className="bg-amber-900/40 rounded-lg p-4 border border-amber-700/30">
                  <p className="text-amber-200/80 text-sm mb-3 font-medium">Plan Features:</p>
                  <ul className="space-y-2">
                    {userData.plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-amber-100 text-sm">
                        <span className="text-green-400 mr-2">✓</span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-amber-900/40 rounded-lg p-4 border border-amber-700/30">
                  <p className="text-amber-200/80 text-sm">
                    <span className="font-medium">Renewal Date:</span> {userData.plan.expiryDate}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Account Actions Card */}
          <div
            className="rounded-2xl border border-amber-700/30 shadow-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(85, 124, 187, 1), rgba(249, 193, 9, 0.7))',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div className="p-6 md:p-8">
              <h3 className="text-xl md:text-2xl font-bold text-amber-100 mb-6">
                Account Actions
              </h3>

              <div className="space-y-4">
                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="w-full bg-black hover:bg-orange-500 text-white font-semibold px-6 py-3 rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02] flex items-center justify-center space-x-2"
                >
                  {/* <span>🚪</span> */}
                  <span>Logout</span>
                </button>

                {/* Delete Account Button */}
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="w-full bg-black hover:bg-red-500 text-white font-semibold px-6 py-3 rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02] flex items-center justify-center space-x-2"
                >
                  {/* <span>⚠️</span> */}
                  <span>Delete Account</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div
            className="w-full max-w-md rounded-2xl border border-red-700/30 shadow-2xl"
            style={{
              background: 'linear-gradient(135deg, rgba(139, 69, 19, 0.95), rgba(101, 67, 33, 0.95))',
            }}
          >
            <div className="p-6 md:p-8">
              <h3 className="text-2xl font-bold text-red-200 mb-4">
                Delete Account?
              </h3>
              <p className="text-red-100/90 text-sm mb-6">
                This action cannot be undone. All your data, including your queries, favorites, and plan information will be permanently deleted.
              </p>

              <div className="mb-6">
                <label className="block text-red-200 text-sm font-medium mb-2">
                  Type <span className="font-bold">DELETE</span> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder="Type DELETE"
                  className="w-full px-4 py-3 rounded-lg bg-red-900/40 border border-red-700/30 text-red-100 placeholder-red-300/50 focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                />
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteConfirmText('');
                  }}
                  className="flex-1 bg-amber-600/80 hover:bg-amber-500 text-white font-semibold px-4 py-3 rounded-lg transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  className="flex-1 bg-red-600/90 hover:bg-red-500 text-white font-semibold px-4 py-3 rounded-lg transition-all"
                >
                  Delete Forever
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ambient dots */}
      <div className="absolute inset-0 z-5 pointer-events-none">
        {Array.from({ length: 15 }).map((_, i) => (
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
    </div>
  );
};

export default ProfilePage;
