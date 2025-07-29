import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation files
import arTranslation from './locales/ar/translation.json';
import enTranslation from './locales/en/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ar: {
        translation: arTranslation
      },
      en: {
        translation: enTranslation
      }
    },
    fallbackLng: 'ar', // Default to Arabic
    debug: process.env.NODE_ENV === 'development',
    
    detection: {
      order: ['localStorage', 'cookie', 'htmlTag', 'path', 'subdomain'],
      caches: ['localStorage'],
    },
    
    interpolation: {
      escapeValue: false // React already does escaping
    }
  });

export default i18n;