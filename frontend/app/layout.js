import './globals.css';

export const metadata = {
  title: 'SpeakSense - Speech Analysis Platform',
  description:
    'Upload and analyse audio files with AI-powered transcription, speaker identification, and emotion detection',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <div className="flex min-h-screen">
          
          {/* Sidebar */}
          <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
            <div className="h-16 flex items-center px-6 border-b border-gray-200">
              <span className="text-lg font-semibold tracking-tight">
                SpeakSense
              </span>
            </div>

            <nav className="flex-1 px-6 py-6 space-y-4 text-sm">
              <div className="text-gray-600 hover:text-black cursor-pointer">
                Dashboard
              </div>
              <div className="text-gray-600 hover:text-black cursor-pointer">
                Reports
              </div>
              <div className="text-gray-600 hover:text-black cursor-pointer">
                Settings
              </div>
            </nav>
          </aside>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col">
            
            {/* Top Header */}
            <header className="h-16 bg-white border-b border-gray-200 flex items-center px-8">
              <h1 className="text-base font-medium tracking-tight">
                Debate Analysis
              </h1>

              <div className="ml-auto">
                <button className="bg-black text-white text-sm px-4 py-2 rounded-lg hover:opacity-90 transition">
                  Download Report
                </button>
              </div>
            </header>

            {/* Page Content */}
            <main className="flex-1 p-8">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}