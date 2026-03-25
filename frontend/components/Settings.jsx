'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const SETTINGS_KEY = 'speaksense_settings';

const defaultSettings = {
  theme: 'light',
  compactDashboard: false,
  defaultStartPage: 'upload',
};

const Settings = () => {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState(defaultSettings);
  const [savedMessage, setSavedMessage] = useState('');

  useEffect(() => {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw);
      setSettings((prev) => ({ ...prev, ...parsed }));
    } catch (error) {
      console.error('Failed to parse settings:', error);
    }
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.classList.toggle('dark', settings.theme === 'dark');
  }, [settings.theme]);

  const handleToggle = (field) => {
    setSettings((prev) => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const handleSave = () => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    setSavedMessage('Settings saved');
    window.setTimeout(() => setSavedMessage(''), 1800);
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(defaultSettings));
    setSavedMessage('Settings reset to defaults');
    window.setTimeout(() => setSavedMessage(''), 1800);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-500 mt-1">Manage your account and app preferences.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-medium text-gray-900 mb-4">Account</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <p><span className="font-medium text-gray-900">Name:</span> {user?.first_name || user?.last_name ? `${user?.first_name || ''} ${user?.last_name || ''}`.trim() : 'Not set'}</p>
          <p><span className="font-medium text-gray-900">Username:</span> {user?.username || 'Not set'}</p>
          <p><span className="font-medium text-gray-900">Email:</span> {user?.email || 'Not set'}</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-medium text-gray-900 mb-4">Preferences</h3>
        <div className="space-y-4">
          <label className="block text-sm text-gray-700">
            <span className="block mb-2">Theme</span>
            <select
              value={settings.theme}
              onChange={(event) => setSettings((prev) => ({ ...prev, theme: event.target.value }))}
              className="w-full md:w-64 border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>

          <label className="flex items-center justify-between text-sm text-gray-700">
            <span>Compact dashboard layout</span>
            <input
              type="checkbox"
              checked={settings.compactDashboard}
              onChange={() => handleToggle('compactDashboard')}
              className="h-4 w-4"
            />
          </label>

          <label className="block text-sm text-gray-700">
            <span className="block mb-2">Default start page</span>
            <select
              value={settings.defaultStartPage}
              onChange={(event) => setSettings((prev) => ({ ...prev, defaultStartPage: event.target.value }))}
              className="w-full md:w-64 border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="upload">Upload</option>
              <option value="reports">Reports</option>
            </select>
          </label>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800"
          >
            Save settings
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
          >
            Reset defaults
          </button>
          {savedMessage && <span className="text-sm text-green-700">{savedMessage}</span>}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-medium text-gray-900 mb-4">Security</h3>
        <p className="text-sm text-gray-600 mb-4">Sign out from your current session.</p>
        <button
          onClick={logout}
          className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default Settings;
