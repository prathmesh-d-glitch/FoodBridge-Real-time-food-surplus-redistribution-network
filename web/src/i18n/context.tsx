import React, { createContext, useContext } from 'react';
import { Language, getTranslation } from './index';

type Translations = ReturnType<typeof getTranslation>;

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export const LanguageProvider: React.FC<{
  language: Language;
  setLanguage: (lang: Language) => void;
  children: React.ReactNode;
}> = ({ language, setLanguage, children }) => {
  const t = getTranslation(language);
  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextValue => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider');
  return ctx;
};
