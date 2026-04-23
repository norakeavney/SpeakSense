'use client';

import { useAuth } from '../contexts/AuthContext';

const AuthenticatedLayout = ({ children, currentPage = 'upload', onPageChange }) => {
  const { user, logout } = useAuth();

  const navigation = [
    { id: 'upload', label: 'Upload', icon: '📤' },
    { id: 'reports', label: 'Reports', icon: '📊' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <span className="text-lg font-semibold tracking-tight">
            SpeakSense
          </span>
        </div>

        <nav className="flex-1 px-6 py-6 space-y-4 text-sm">
          {navigation.map((item) => (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`w-full text-left flex items-center space-x-3 px-3 py-2 rounded-md transition ${
                currentPage === item.id
                  ? 'bg-gray-100 text-black font-medium'
                  : 'text-gray-600 hover:text-black hover:bg-gray-50'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="border-t border-gray-200 p-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-black text-white rounded-full flex items-center justify-center text-sm font-medium">
              {user?.first_name?.[0] || user?.username?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.first_name && user?.last_name 
                  ? `${user.first_name} ${user.last_name}`
                  : user?.username || 'User'
                }
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-4 w-full text-left text-sm text-gray-600 hover:text-black"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-8">
          <h1 className="text-base font-medium tracking-tight">
            {navigation.find(item => item.id === currentPage)?.label || 'SpeakSense'}
          </h1>

          <div className="ml-auto flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              Welcome, {user?.first_name || user?.username}!
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AuthenticatedLayout;