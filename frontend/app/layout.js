import './globals.css';
import { AuthProvider } from '../contexts/AuthContext';

export const metadata = {
  title: 'SpeakSense - Speech Analysis Platform',
  description:
    'Upload and analyse audio files with AI-powered transcription, speaker identification, and emotion detection',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}