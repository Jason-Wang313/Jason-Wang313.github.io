(function () {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ===== ROTATING TEXT =====
  const phrases = [
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

  const rotatingEl = document.getElementById('rotating-text');
  if (rotatingEl && !prefersReducedMotion) {
    let idx = 0;
    setInterval(function () {
      rotatingEl.classList.add('slide-out');
      setTimeout(function () {
        idx = (idx + 1) % phrases.length;
        rotatingEl.textContent = phrases[idx];
        rotatingEl.classList.remove('slide-out');
        rotatingEl.classList.add('slide-in-prepare');
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            rotatingEl.classList.remove('slide-in-prepare');
          });
        });
      }, 450);
    }, 3000);
  }

  // ===== NAVBAR SCROLL BEHAVIOR =====
  const navbar = document.getElementById('navbar');
  const hero = document.getElementById('hero');

  if (navbar && hero) {
    const heroObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          navbar.classList.toggle('navbar--scrolled', !entry.isIntersecting);
        });
      },
      { threshold: 0.05 }
    );
    heroObserver.observe(hero);
  }

  // ===== ACTIVE NAV LINK =====
  const navLinks = document.querySelectorAll('.navbar__links a[href^="#"]');
  const sections = [];
  navLinks.forEach(function (link) {
    const id = link.getAttribute('href').slice(1);
    const section = document.getElementById(id);
    if (section) sections.push({ el: section, link: link });
  });

  if (sections.length > 0) {
    const sectionObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            navLinks.forEach(function (l) { l.classList.remove('active'); });
            var match = sections.find(function (s) { return s.el === entry.target; });
            if (match) match.link.classList.add('active');
          }
        });
      },
      { threshold: 0.3, rootMargin: '-80px 0px -50% 0px' }
    );
    sections.forEach(function (s) { sectionObserver.observe(s.el); });
  }

  // ===== MOBILE HAMBURGER =====
  const toggle = document.querySelector('.navbar__toggle');
  const navLinksContainer = document.querySelector('.navbar__links');

  if (toggle && navLinksContainer) {
    toggle.addEventListener('click', function () {
      navLinksContainer.classList.toggle('open');
      toggle.closest('.navbar').classList.toggle('nav-open');
    });

    navLinksContainer.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinksContainer.classList.remove('open');
        toggle.closest('.navbar').classList.remove('nav-open');
      });
    });
  }

  // ===== FADE-IN OBSERVER =====
  var fadeEls = document.querySelectorAll('.fade-in');

  if (prefersReducedMotion) {
    fadeEls.forEach(function (el) { el.classList.add('visible'); });
  } else if (fadeEls.length > 0) {
    var fadeObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    fadeEls.forEach(function (el) { fadeObserver.observe(el); });
  }
})();
