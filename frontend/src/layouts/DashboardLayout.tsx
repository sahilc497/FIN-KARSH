import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { DisclaimerFooter } from '../components/DisclaimerFooter';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 font-sans">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
      <DisclaimerFooter />
    </div>
  );
};

