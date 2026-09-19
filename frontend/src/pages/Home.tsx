import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiFetch } from '../api/client';
import type { TopicOut } from '../api/types';

interface HomeProps {
  onReOnboard: () => void;
}

export const Home: React.FC<HomeProps> = ({ onReOnboard }) => {
  const { user, logout } = useAuth();
  const [topics, setTopics] = useState<TopicOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<TopicOut[]>('/topics')
      .then((data) => {
        setTopics(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch topics');
        setLoading(false);
      });
  }, []);

  const userAvatar = user?.user_metadata?.avatar_url || user?.user_metadata?.picture;
  const username = user?.email?.split('@')[0] || 'Student';

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '24px', textAlign: 'left' }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '20px 24px',
        borderRadius: '16px',
        background: 'var(--code-bg, #1f2028)',
        border: '1px solid var(--border, #2e303a)',
        marginBottom: '32px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {userAvatar ? (
            <img
              src={userAvatar}
              alt="Avatar"
              style={{ width: '48px', height: '48px', borderRadius: '50%' }}
            />
          ) : (
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'var(--accent, #a855f7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '20px',
              color: '#fff',
            }}>
              {username[0]?.toUpperCase()}
            </div>
          )}
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', color: 'var(--text-h)' }}>
              Welcome back, {username}!
            </h2>
            <div style={{ fontSize: '13px', color: 'var(--text)', marginTop: '2px' }}>
              {user?.email}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={onReOnboard}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text)',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Edit Onboarding
          </button>
          <button
            onClick={logout}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: 'rgba(239, 68, 68, 0.2)',
              color: '#f87171',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '14px',
            }}
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content */}
      <h2 style={{ fontSize: '24px', marginBottom: '16px', color: 'var(--text-h)' }}>
        Your Topic Mastery & Progression
      </h2>

      {loading && <p>Loading topic levels...</p>}

      {error && (
        <div style={{
          padding: '12px',
          borderRadius: '8px',
          background: 'rgba(239, 68, 68, 0.15)',
          color: '#f87171',
          marginBottom: '16px',
        }}>
          {error}
        </div>
      )}

      {!loading && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '16px',
        }}>
          {topics.map((topic) => {
            const hasProgress = topic.current_level !== null;
            return (
              <div
                key={topic.id}
                style={{
                  padding: '20px',
                  borderRadius: '12px',
                  background: 'var(--code-bg, #1f2028)',
                  border: `1px solid ${hasProgress ? 'var(--accent, #a855f7)' : 'var(--border, #2e303a)'}`,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '18px', color: 'var(--text-h)', marginBottom: '8px' }}>
                  {topic.name}
                </div>
                {hasProgress ? (
                  <div style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '20px',
                    background: 'rgba(168, 85, 247, 0.2)',
                    color: 'var(--accent, #c084fc)',
                    fontWeight: 700,
                    fontSize: '14px',
                  }}>
                    Level {topic.current_level}
                  </div>
                ) : (
                  <div style={{ fontSize: '13px', color: 'var(--text)' }}>
                    Not Selected in Onboarding
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
