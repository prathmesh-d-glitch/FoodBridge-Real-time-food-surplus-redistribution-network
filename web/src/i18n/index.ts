import en from './en.json';
import hi from './hi.json';
import kn from './kn.json';

export type Language = 'en' | 'hi' | 'kn';

export const translations = {
  en,
  hi,
  kn,
};

export const getTranslation = (lang: Language) => {
  return translations[lang] || translations.en;
};
