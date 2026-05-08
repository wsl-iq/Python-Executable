// تفعيل القائمة للموبايل
const toggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');
if (toggle) {
  toggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    toggle.classList.toggle('active');
  });
}

// تأثير التمرير على النافبار
window.addEventListener('scroll', () => {
  document.querySelector('.navbar').classList.toggle('scrolled', window.scrollY > 50);
});

// مراقب ظهور العناصر (fade-up)
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting));
}, { threshold: 0.1 });
document.querySelectorAll('.fade-up, .card, .lang-item, .review-card').forEach(el => observer.observe(el));

// إمالة بسيطة (tilt) للصور والبطاقات
document.querySelectorAll('.tilt').forEach(c => {
  c.addEventListener('mousemove', e => {
    const rect = c.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    c.style.transform = `perspective(800px) rotateX(${-y / 25}deg) rotateY(${x / 25}deg) scale(1.02)`;
  });
  c.addEventListener('mouseleave', () => c.style.transform = '');
});

// سلاسة التمرير للروابط الداخلية
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      window.scrollTo({ top: target.offsetTop - 70, behavior: 'smooth' });
      if (navLinks.classList.contains('active')) {
        navLinks.classList.remove('active');
        if (toggle) toggle.classList.remove('active');
      }
    }
  });
});

// تفعيل خاصية التقييم (يمكن ربطها بـ API لاحقاً)
console.log('PyToExe - الصفحة جاهزة');