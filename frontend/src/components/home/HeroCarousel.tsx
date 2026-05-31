import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const slides = [
  {
    image: '/hero/hero1.png',
    titleKey: 'hero.slide1Title',
    subtitleKey: 'hero.slide1Subtitle',
    buttonKey: 'hero.slide1Cta',
  },
  {
    image: '/hero/hero2.png',
    titleKey: 'hero.slide2Title',
    subtitleKey: 'hero.slide2Subtitle',
    buttonKey: 'hero.slide2Cta',
  },
  {
    image: '/hero/hero3.png',
    titleKey: 'hero.slide3Title',
    subtitleKey: 'hero.slide3Subtitle',
    buttonKey: 'hero.slide3Cta',
  },
];

export const HeroCarousel: React.FC = () => {
  const [current, setCurrent] = useState(0);
  const { t } = useTranslation();

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrent((value) => (value + 1) % slides.length);
    }, 5500);

    return () => window.clearInterval(timer);
  }, []);

  const next = () => setCurrent((value) => (value + 1) % slides.length);
  const previous = () => setCurrent((value) => (value - 1 + slides.length) % slides.length);

  return (
    <section className="hero-carousel">
      {slides.map((slide, index) => (
        <article
          key={slide.titleKey}
          className={`hero-slide ${index === current ? 'active' : ''}`}
          style={{ backgroundImage: `url(${slide.image})` }}
        >
          <div className="hero-overlay" />
          <div className={`hero-content ${index === current ? 'active' : ''}`}>
            <h1>{t(slide.titleKey)}</h1>
            <p>{t(slide.subtitleKey)}</p>
            <Link className="hero-cta" to="/products">{t(slide.buttonKey)}</Link>
          </div>
        </article>
      ))}

      <button className="hero-nav hero-prev" onClick={previous} aria-label={t('common.previous')}>
        <ChevronLeft />
      </button>
      <button className="hero-nav hero-next" onClick={next} aria-label={t('common.next')}>
        <ChevronRight />
      </button>

      <div className="hero-dots">
        {slides.map((slide, index) => (
          <button key={slide.titleKey} className={index === current ? 'active' : ''} onClick={() => setCurrent(index)} aria-label={t(slide.titleKey)} />
        ))}
      </div>
    </section>
  );
};
