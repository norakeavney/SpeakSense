import './globals.css';

export const metadata = {
  title: 'SpeakSense - Speech Analysis Platform',
  description: 'Upload and analyze audio files with AI-powered transcription, speaker identification, and emotion detection',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
