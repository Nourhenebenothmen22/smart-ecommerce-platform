import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useDirection } from '../../hooks/useDirection';
import { Button } from '../ui/Button';

export const TopHeroCarousel: React.FC = () => {
  const { t } = useTranslation();
  const dir = useDirection();
  const [current, setCurrent] = useState(0);
  const [paused, setPaused] = useState(false);

  const slides = useMemo(
    () => [
      { title: t('hero.slide1Title'), subtitle: t('hero.slide1Subtitle'), cta: t('hero.slide1Cta'), image: '/images/hero/hero_slide_1.png' },
      { title: t('hero.slide2Title'), subtitle: t('hero.slide2Subtitle'), cta: t('hero.slide2Cta'), image: '/images/hero/hero_slide_1.png' },
      { title: t('hero.slide3Title'), subtitle: t('hero.slide3Subtitle'), cta: t('hero.slide3Cta'), image: '/images/hero/hero_slide_1.png' },
    ],
    [t]
  );

  useEffect(() => {
    if (paused) return undefined;
    const timer = window.setInterval(() => setCurrent((prev) => (prev + 1) % slides.length), 6000);
    return () => window.clearInterval(timer);
  }, [paused, slides.length]);

  const next = () => setCurrent((prev) => (prev + 1) % slides.length);
  const prev = () => setCurrent((prev) => (prev - 1 + slides.length) % slides.length);

  return (
    <section className="hero-carousel" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      {slides.map((slide, index) => (
        <article key={slide.title} className={`hero-slide ${index === current ? 'is-active' : ''}`}>
          <div className="hero-copy">
            <h1>{slide.title}</h1>
            <p>{slide.subtitle}</p>
            <Button variant="primary" onClick={() => { window.location.href = '/products'; }}>{slide.cta}</Button>
          </div>
          <img src={slide.image} alt={slide.title} />
        </article>
      ))}

      <button className="hero-arrow hero-arrow-prev" onClick={dir === 'rtl' ? next : prev} aria-label={t('common.previous')}>
        <ChevronLeft className="icon-flip" />
      </button>
      <button className="hero-arrow hero-arrow-next" onClick={dir === 'rtl' ? prev : next} aria-label={t('common.next')}>
        <ChevronRight className="icon-flip" />
      </button>

      <div className="hero-dots">
        {slides.map((slide, index) => (
          <button key={slide.title} className={index === current ? 'is-active' : ''} onClick={() => setCurrent(index)} aria-label={`${t('common.next')} ${index + 1}`} />
        ))}
      </div>
    </section>
  );
};
