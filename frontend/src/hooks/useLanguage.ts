import { useTranslation } from 'react-i18next';

export type Language = 'en' | 'fr' | 'ar';

export interface LanguageOption {
  code: Language;
  name: string;
  dir: 'ltr' | 'rtl';
}

export const languages: LanguageOption[] = [
  { code: 'en', name: 'English', dir: 'ltr' },
  { code: 'fr', name: 'Francais', dir: 'ltr' },
  { code: 'ar', name: 'Arabic', dir: 'rtl' },
];

export function useLanguage() {
  const { i18n } = useTranslation();

  const changeLanguage = async (code: Language) => {
    await i18n.changeLanguage(code);
    const selected = languages.find((language) => language.code === code);
    if (selected) {
      document.documentElement.lang = selected.code;
      document.documentElement.dir = selected.dir;
      localStorage.setItem('darstore-language', code);
    }
  };

  return {
    language: (i18n.language || 'en') as Language,
    changeLanguage,
    languages,
  };
}
