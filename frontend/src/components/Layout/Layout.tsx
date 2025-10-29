import { Outlet } from 'react-router-dom';
import Sidebar from '../ui/Sidebar';
import { Toaster } from 'react-hot-toast';

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <main className="lg:pl-64 pt-16 lg:pt-0">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
      <Toaster position="top-right" />
    </div>
  );
}