import { useState, useEffect } from 'react';
import { useAuth } from './hooks/useAuth';
import { Login } from './pages/Login';
import { Onboarding } from './pages/Onboarding';
import { Home } from './pages/Home';
import { apiFetch } from './api/client';
import type { TopicOut } from './api/types';
import './App.css';

export function App() {
  const { session, user, loading: authLoading } = useAuth();
  const [isOnboarded, setIsOnboarded] = useState<boolean | null>(null);
  const [checkingOnboarding, setCheckingOnboarding] = useState<boolean>(false);

  useEffect(() => {
    if (session && user) {
      setCheckingOnboarding(true);
      apiFetch<TopicOut[]>('/topics')
        .then((topics) => {
          const hasAnyLevel = topics.some((t) => t.current_level !== null);
          setIsOnboarded(hasAnyLevel);
          setCheckingOnboarding(false);
        })
        .catch(() => {
          setIsOnboarded(false);
          setCheckingOnboarding(false);
        });
    } else {
      setIsOnboarded(null);
    }
  }, [session, user]);

  if (authLoading || (session && checkingOnboarding)) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        color: 'var(--text-h)',
      }}>
        <h2>Loading PARAKH Session...</h2>
      </div>
    );
  }

  if (!session || !user) {
    return <Login />;
  }

  if (isOnboarded === false) {
    return <Onboarding onComplete={() => setIsOnboarded(true)} />;
  }

  return <Home onReOnboard={() => setIsOnboarded(false)} />;
}

export default App;
