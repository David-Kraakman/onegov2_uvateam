import { Code2 } from 'lucide-react';
import { navigationPages, repoUrl } from '../constants/appConstants';
import type { Page } from '../types';

type NavbarProps = {
  activePage: Page;
  onPageChange: (page: Page) => void;
};

export function Navbar({ activePage, onPageChange }: NavbarProps) {
  return (
    <nav className="liquid-glass shrink-0 rounded-xl px-6 py-3">
      <div className="relative z-10 flex items-center justify-between gap-6">
        <button className="text-2xl font-semibold tracking-tight" onClick={() => onPageChange('Simulatie')}>Sick Sim</button>
        <div className="hidden items-center gap-8 md:flex">
          {navigationPages.map((page) => (
            <button key={page} onClick={() => onPageChange(page)} className={`border-b py-1 text-sm transition hover:text-gray-300 ${activePage === page || (page === 'Simulatie' && activePage === 'Simulatie run') ? 'border-white text-white' : 'border-transparent text-white/70'}`}>
              {page}
            </button>
          ))}
        </div>
        <a href={repoUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2 text-sm font-medium text-black transition hover:bg-gray-100">
          <Code2 size={16} /> GitHub-code
        </a>
      </div>
    </nav>
  );
}
