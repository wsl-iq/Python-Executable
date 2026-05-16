document.addEventListener('DOMContentLoaded', () => {
  function setLanguageDirection(lang) {
    const isEnglish = lang.toLowerCase().startsWith('en');
    const direction = isEnglish ? 'ltr' : 'rtl';
    document.documentElement.setAttribute('dir', direction);
    localStorage.setItem('preferred_direction', direction);
  }

  function initializeDirection() {
    const userLang = navigator.language || navigator.userLanguage || 'en';
    setLanguageDirection(userLang);
  }

  function restoreDirectionPreference() {
    const savedDirection = localStorage.getItem('preferred_direction');
    if (savedDirection) {
      document.documentElement.setAttribute('dir', savedDirection);
    } else {
      initializeDirection();
    }
  }

  function handleResponsiveNav() {
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;
    if (window.innerWidth <= 768) {
      navLinks.classList.add('mobile-ready');
    } else {
      navLinks.classList.remove('mobile-ready', 'active');
    }
  }

  function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  restoreDirectionPreference();

  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navbar = document.querySelector('.navbar');

  if (toggle && navLinks) {
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      navLinks.classList.toggle('active');
      const isExpanded = navLinks.classList.contains('active');
      toggle.setAttribute('aria-expanded', isExpanded);
    });

    document.addEventListener('click', (e) => {
      if (!navLinks.contains(e.target) && !toggle.contains(e.target)) {
        navLinks.classList.remove('active');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navLinks.classList.contains('active')) {
        navLinks.classList.remove('active');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });

    navLinks.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link) {
        const linkText = link.textContent.trim().toLowerCase();
        if (linkText.includes('english')) {
          setLanguageDirection('en');
        } else if (linkText.includes('العربية')) {
          setLanguageDirection('ar');
        }
        if (window.innerWidth <= 768) {
          navLinks.classList.remove('active');
          toggle.setAttribute('aria-expanded', 'false');
        }
      }
    });
  }

  if (navbar) {
    const handleScroll = throttle(() => {
      const shouldShowScrolled = window.scrollY > 50;
      navbar.classList.toggle('scrolled', shouldShowScrolled);
      if (shouldShowScrolled) {
        navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.3)';
      } else {
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
      }
    }, 10);

    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const animationObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        const siblings = entry.target.parentElement?.children;
        if (siblings) {
          Array.from(siblings).forEach((sibling, index) => {
            if (sibling.classList.contains('fade-up')) {
              sibling.style.transitionDelay = `${index * 0.1}s`;
            }
          });
        }
        animationObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  const animatableElements = document.querySelectorAll(
    '.fade-up, .card, .lang-item, .review-card, .feature-category, .option-item, .support-card'
  );
  animatableElements.forEach((el) => animationObserver.observe(el));

  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        const navbarHeight = navbar ? navbar.offsetHeight : 70;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
        history.pushState(null, null, targetId);
        if (navLinks) {
          navLinks.classList.remove('active');
          if (toggle) toggle.setAttribute('aria-expanded', 'false');
        }
      }
    });
  });

  const themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    const applyTheme = (theme) => {
      if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        themeToggle.setAttribute('aria-label', 'تفعيل الوضع النهاري');
      } else {
        document.body.classList.remove('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        themeToggle.setAttribute('aria-label', 'تفعيل الوضع الليلي');
      }
    };

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      applyTheme(savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      applyTheme(prefersDark ? 'dark' : 'light');
    }

    themeToggle.addEventListener('click', () => {
      const isDarkMode = document.body.classList.contains('dark-mode');
      const newTheme = isDarkMode ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('theme', newTheme);
    });

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  handleResponsiveNav();

  document.querySelectorAll('.btn-3d, button, .nav-toggle').forEach((btn) => {
    btn.addEventListener('touchstart', function(e) {
      e.preventDefault();
      this.click();
    }, { passive: false });
  });

  document.addEventListener('keydown', (e) => {
    if (e.altKey && !e.ctrlKey && !e.metaKey) {
      const sections = document.querySelectorAll('section[id]');
      const sectionIndex = parseInt(e.key) - 1;
      if (sectionIndex >= 0 && sectionIndex < sections.length) {
        e.preventDefault();
        sections[sectionIndex].scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  const lazyImages = document.querySelectorAll('img[loading="lazy"]');
  if ('loading' in HTMLImageElement.prototype) {
    lazyImages.forEach((img) => {
      img.src = img.dataset.src;
    });
  } else {
    const lazyImageObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.add('loaded');
          lazyImageObserver.unobserve(img);
        }
      });
    });
    lazyImages.forEach((img) => lazyImageObserver.observe(img));
  }

  if (window.performance && window.performance.getEntriesByType) {
    window.addEventListener('load', () => {
      const navigationEntry = performance.getEntriesByType('navigation')[0];
      if (navigationEntry) {
        console.log(`وقت تحميل الصفحة: ${navigationEntry.loadEventEnd - navigationEntry.startTime}ms`);
      }
    });
  }

  window.addEventListener('error', (e) => {
    if (e.target.tagName === 'LINK' || e.target.tagName === 'SCRIPT') {
      console.warn(`فشل تحميل المورد: ${e.target.src || e.target.href}`);
    }
  }, true);

});

window.addEventListener('resize', throttle(handleResponsiveNav, 200));

window.addEventListener('languagechange', () => {
  initializeDirection();
});

if (typeof window !== 'undefined') {
  window.PyToExe = {
    setDirection: setLanguageDirection,
    toggleTheme: () => {
      const event = new Event('click');
      document.querySelector('.theme-toggle')?.dispatchEvent(event);
    },
    scrollToSection: (sectionId) => {
      const section = document.querySelector(sectionId);
      if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
      }
    },
    resetPreferences: () => {
      localStorage.clear();
      location.reload();
    }
  };
}

console.log('From Python To Executable');