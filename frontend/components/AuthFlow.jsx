'use client';

import { useState } from 'react';
import Login from './Login';
import Register from './Register';

const AuthFlow = ({ onSuccess }) => {
  const [currentForm, setCurrentForm] = useState('login');

  return (
    <>
      {currentForm === 'login' ? (
        <Login
          onSwitchToRegister={() => setCurrentForm('register')}
          onSuccess={onSuccess}
        />
      ) : (
        <Register
          onSwitchToLogin={() => setCurrentForm('login')}
          onSuccess={onSuccess}
        />
      )}
    </>
  );
};

export default AuthFlow;