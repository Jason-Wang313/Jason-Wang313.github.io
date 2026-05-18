(function () {
  const interests = [
    'Physical World Models',
    'Embodied AI',
    'Robot Learning',
    'Compositional Generalization',
    'Object-Centric Representations',
    'Energy-Based Inference',
    'Novelty Detection',
    'Active Exploration',
    'Continual Learning',
    'Sim-to-Real Adaptation',
  ];

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const header = document.querySelector('.site-header');
  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.site-nav');
  const rotating = document.getElementById('rotating-interest');

  function syncHeader() {
    if (!header) return;
    header.classList.toggle('is-scrolled', window.scrollY > 24);
  }

  syncHeader();
  window.addEventListener('scroll', syncHeader, { passive: true });

  if (navToggle && header && nav) {
    navToggle.addEventListener('click', function () {
      const isOpen = header.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(isOpen));
    });

    nav.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        header.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  if (rotating && !prefersReducedMotion) {
    let index = 0;
    window.setInterval(function () {
      rotating.classList.add('is-swapping');
      window.setTimeout(function () {
        index = (index + 1) % interests.length;
        rotating.textContent = interests[index];
        rotating.classList.remove('is-swapping');
      }, 260);
    }, 2800);
  }

  const revealEls = document.querySelectorAll('.reveal');
  if (prefersReducedMotion) {
    revealEls.forEach(function (el) {
      el.classList.add('is-visible');
    });
  } else if (revealEls.length) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16, rootMargin: '0px 0px -40px 0px' }
    );

    revealEls.forEach(function (el) {
      observer.observe(el);
    });
  }

  const navLinks = document.querySelectorAll('.site-nav a[href^="#"]');
  const sections = Array.from(navLinks)
    .map(function (link) {
      return {
        link: link,
        section: document.querySelector(link.getAttribute('href')),
      };
    })
    .filter(function (item) {
      return item.section;
    });

  if (sections.length) {
    const activeObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            navLinks.forEach(function (link) {
              link.classList.remove('is-active');
            });
            const match = sections.find(function (item) {
              return item.section === entry.target;
            });
            if (match) match.link.classList.add('is-active');
          }
        });
      },
      { threshold: 0.22, rootMargin: '-80px 0px -54% 0px' }
    );

    sections.forEach(function (item) {
      activeObserver.observe(item.section);
    });
  }
})();
