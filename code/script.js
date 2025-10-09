document.addEventListener('DOMContentLoaded', function() {
    const langToggle = document.getElementById('langToggle');
    const htmlElement = document.querySelector('html');
    const bodyElement = document.querySelector('body');
    
    const savedLang = localStorage.getItem('preferredLang') || 'ar';
    setLanguage(savedLang);
    
    langToggle.addEventListener('click', function() {
        const currentLang = htmlElement.getAttribute('lang');
        const newLang = currentLang === 'ar' ? 'en' : 'ar';
        setLanguage(newLang);
        localStorage.setItem('preferredLang', newLang);
    });
    
    function setLanguage(lang) {
        htmlElement.setAttribute('lang', lang);
        htmlElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        bodyElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        
        updateTexts(lang);
        
        langToggle.textContent = lang === 'ar' ? 'EN' : 'AR';
    }
    
    function updateTexts(lang) {
        const elements = document.querySelectorAll('[data-ar], [data-en]');
        
        elements.forEach(element => {
            const text = lang === 'ar' ? 
                element.getAttribute('data-ar') : 
                element.getAttribute('data-en');
            
            if (text) {
                element.textContent = text;
            }
        });
    }
    
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            navLinks.classList.remove('active');
        });
    });
    
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.backgroundColor = 'var(--bg-color)';
            navbar.style.backdropFilter = 'none';
        }
    });
    
    loadGitHubStats();
    
    function loadGitHubStats() {
        fetch('https://api.github.com/repos/wsl-iq/Python-Executable')
            .then(response => response.json())
            .then(data => {
                document.getElementById('stars').textContent = data.stargazers_count;
                document.getElementById('forks').textContent = data.forks_count;
                document.getElementById('watchers').textContent = data.watchers_count;
            })
            .catch(error => {
                console.error('Error fetching GitHub data:', error);
            }); 
    }
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.feature-card, .download-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
});