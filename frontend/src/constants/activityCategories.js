export const ACTIVITY_CATEGORIES = [
  {
    key: 'research',
    label: 'Research',
    description: 'IRB studies, data collection, analysis, manuscripts.',
    tone: 'blue',
  },
  {
    key: 'teaching',
    label: 'Teaching',
    description: 'Course materials, lectures, classroom activities, syllabi.',
    tone: 'green',
  },
  {
    key: 'grading',
    label: 'Grading',
    description: 'Essay grading, rubric scoring, feedback on student work.',
    tone: 'orange',
  },
  {
    key: 'admin',
    label: 'Admin',
    description: 'Committee work, reviews, reports, administrative tasks.',
    tone: 'purple',
  },
];

export const CATEGORY_LABELS = Object.fromEntries(
  ACTIVITY_CATEGORIES.map((c) => [c.key, c.label]),
);

export const CATEGORY_TONES = Object.fromEntries(
  ACTIVITY_CATEGORIES.map((c) => [c.key, c.tone]),
);

export function getCategoryLabel(key) {
  return CATEGORY_LABELS[key] || null;
}

export function getCategoryTone(key) {
  return CATEGORY_TONES[key] || null;
}
