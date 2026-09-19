import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import type { TopicOut, OnboardingResponse } from '../api/types';

interface OnboardingProps {
  onComplete: () => void;
}

export const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const [topics, setTopics] = useState<TopicOut[]>([]);
  const [selectedTopicIds, setSelectedTopicIds] = useState<number[]>([]);
  const [selfAssessments, setSelfAssessments] = useState<Record<number, 'beginner' | 'intermediate' | 'advanced'>>({});
  const [collegeYear, setCollegeYear] = useState<string>('3rd Year');
  const [stream, setStream] = useState<string>('Computer Science');
  const [goal, setGoal] = useState<string>('');
  const [userTimezone, setUserTimezone] = useState<string>('UTC');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [loadingTopics, setLoadingTopics] = useState<boolean>(true);

  useEffect(() => {
    // Detect browser timezone
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (tz) setUserTimezone(tz);
    } catch {
      setUserTimezone('UTC');
    }

    // Fetch topics from backend
    apiFetch<TopicOut[]>('/topics')
      .then((data) => {
        setTopics(data);
        setLoadingTopics(false);
      })
      .catch(() => {
        // Fallback default V1 topics if unauthenticated initial fetch
        setTopics([
          { id: 1, name: 'DSA', current_level: null },
          { id: 2, name: 'Operating Systems', current_level: null },
          { id: 3, name: 'DBMS', current_level: null },
          { id: 4, name: 'Computer Networks', current_level: null },
          { id: 5, name: 'System Design', current_level: null },
        ]);
        setLoadingTopics(false);
      });
  }, []);

  const toggleTopic = (id: number) => {
    if (selectedTopicIds.includes(id)) {
      setSelectedTopicIds(selectedTopicIds.filter((tId) => tId !== id));
      const updatedAssessments = { ...selfAssessments };
      delete updatedAssessments[id];
      setSelfAssessments(updatedAssessments);
    } else {
      setSelectedTopicIds([...selectedTopicIds, id]);
      setSelfAssessments({
        ...selfAssessments,
        [id]: 'intermediate',
      });
    }
  };

  const handleAssessmentChange = (id: number, level: 'beginner' | 'intermediate' | 'advanced') => {
    setSelfAssessments({
      ...selfAssessments,
      [id]: level,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTopicIds.length < 3) {
      setError('Please select at least 3 topics to continue.');
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        topic_selections: selectedTopicIds.map((id) => ({
          topic_id: id,
          self_assessment: selfAssessments[id] || 'intermediate',
        })),
        academic_info: {
          college_year: collegeYear,
          stream,
        },
        goal: goal || undefined,
        timezone: userTimezone,
      };

      await apiFetch<OnboardingResponse>('/onboarding', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      onComplete();
    } catch (err: any) {
      setError(err.message || 'Failed to complete onboarding');
      setSubmitting(false);
    }
  };

  if (loadingTopics) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>Loading Onboarding Options...</h2>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '720px',
      margin: '40px auto',
      padding: '32px',
      borderRadius: '16px',
      background: 'var(--code-bg, #1f2028)',
      border: '1px solid var(--border, #2e303a)',
      textAlign: 'left',
    }}>
      <h1 style={{ fontSize: '28px', marginTop: 0, color: 'var(--text-h)' }}>
        Welcome to PARAKH! 🚀
      </h1>
      <p style={{ color: 'var(--text)', marginBottom: '24px' }}>
        Let's personalize your interview experience. Pick at least 3 core topics to get started at <strong>Level 1</strong>.
      </p>

      {error && (
        <div style={{
          padding: '12px 16px',
          marginBottom: '20px',
          borderRadius: '8px',
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Topic Selection */}
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>
            1. Select Topics (Select 3 or more) *
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {topics.map((t) => {
              const isSelected = selectedTopicIds.includes(t.id);
              return (
                <div
                  key={t.id}
                  onClick={() => toggleTopic(t.id)}
                  style={{
                    padding: '16px',
                    borderRadius: '10px',
                    border: `2px solid ${isSelected ? 'var(--accent, #a855f7)' : 'var(--border, #374151)'}`,
                    background: isSelected ? 'rgba(168, 85, 247, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    cursor: 'pointer',
                    userSelect: 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--text-h)' }}>{t.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>
                    {isSelected ? '✓ Selected' : '+ Click to select'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Self Assessment per selected topic */}
        {selectedTopicIds.length > 0 && (
          <div style={{ marginBottom: '28px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>
              2. Self-Assessed Skill Level per Topic
            </h2>
            {selectedTopicIds.map((id) => {
              const topicObj = topics.find((t) => t.id === id);
              return (
                <div key={id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)' }}>
                  <span style={{ fontWeight: 500, color: 'var(--text-h)' }}>{topicObj?.name}</span>
                  <select
                    value={selfAssessments[id] || 'intermediate'}
                    onChange={(e) => handleAssessmentChange(id, e.target.value as any)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      background: '#2d2f3d',
                      color: '#ffffff',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              );
            })}
          </div>
        )}

        {/* Academic Info */}
        <div style={{ marginBottom: '28px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 500 }}>College Year *</label>
            <select
              value={collegeYear}
              onChange={(e) => setCollegeYear(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '8px',
                background: '#2d2f3d',
                color: '#ffffff',
                border: '1px solid var(--border)',
              }}
            >
              <option value="1st Year">1st Year</option>
              <option value="2nd Year">2nd Year</option>
              <option value="3rd Year">3rd Year</option>
              <option value="4th Year">4th Year</option>
              <option value="Postgraduate">Postgraduate</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 500 }}>Stream / Branch *</label>
            <input
              type="text"
              value={stream}
              onChange={(e) => setStream(e.target.value)}
              placeholder="e.g. CSE, IT, ECE"
              required
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '8px',
                background: '#2d2f3d',
                color: '#ffffff',
                border: '1px solid var(--border)',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>

        {/* Goal / Intent */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 500 }}>Goal / Intent (Optional)</label>
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Placement preparation, Placement practice, DSA prep"
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              background: '#2d2f3d',
              color: '#ffffff',
              border: '1px solid var(--border)',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Detected Timezone Display */}
        <div style={{ marginBottom: '28px', fontSize: '13px', color: 'var(--text)' }}>
          Timezone detected: <code>{userTimezone}</code>
        </div>

        <button
          type="submit"
          disabled={submitting || selectedTopicIds.length < 3}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '10px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: submitting || selectedTopicIds.length < 3 ? 'not-allowed' : 'pointer',
            backgroundColor: 'var(--accent, #a855f7)',
            color: '#ffffff',
            border: 'none',
            opacity: submitting || selectedTopicIds.length < 3 ? 0.6 : 1,
            transition: 'all 0.2s ease',
          }}
        >
          {submitting ? 'Saving Onboarding...' : 'Complete Onboarding & Get Started'}
        </button>
      </form>
    </div>
  );
};
