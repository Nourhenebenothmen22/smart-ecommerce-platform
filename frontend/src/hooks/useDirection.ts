import { useTranslation } from 'react-i18next';

export function useDirection() {
  const { i18n } = useTranslation();
  const lang = i18n.language || 'en';
  return lang.startsWith('ar') ? 'rtl' : 'ltr';
}
