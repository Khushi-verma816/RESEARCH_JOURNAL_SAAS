/* ═══════════════════════════════════════════════════════
   RESEARCH HUB — PREMIUM ANIMATIONS ENGINE
   Runs after DOM ready
═══════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ── 1. PAGE LOADER ─────────────────────────────────── */
    var loader = document.getElementById('page-loader');
    if (loader) {
        window.addEventListener('load', function () {
            setTimeout(function () {
                loader.classList.add('hidden');
                setTimeout(function () { loader.remove(); }, 700);
            }, 400);
        });
    }

    /* ── 2. SCROLL PROGRESS BAR ─────────────────────────── */
    var progressBar = document.getElementById('scroll-progress');
    if (progressBar) {
        window.addEventListener('scroll', function () {
            var scrolled = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
            progressBar.style.width = Math.min(scrolled, 100) + '%';
        }, { passive: true });
    }

    /* ── 3. CURSOR GLOW (desktop only) ─────────────────── */
    var glow = document.getElementById('cursor-glow');
    if (glow && window.innerWidth > 768) {
        var glowX = 0, glowY = 0, curX = 0, curY = 0;
        document.addEventListener('mousemove', function (e) {
            glowX = e.clientX; glowY = e.clientY;
        });
        function animateGlow() {
            curX += (glowX - curX) * 0.08;
            curY += (glowY - curY) * 0.08;
            glow.style.left = curX + 'px';
            glow.style.top  = curY + 'px';
            requestAnimationFrame(animateGlow);
        }
        animateGlow();
    }

    /* ── 4. ENHANCED PARTICLE CANVAS (with connections) ─── */
    var canvas = document.getElementById('hero-canvas');
    if (canvas) {
        var ctx = canvas.getContext('2d');
        var particles = [];
        var COUNT = 70;
        var CONNECT_DIST = 130;
        var mouse = { x: -9999, y: -9999 };

        function resize() {
            canvas.width  = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }
        resize();
        window.addEventListener('resize', resize, { passive: true });

        canvas.parentElement.addEventListener('mousemove', function (e) {
            var rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
        });
        canvas.parentElement.addEventListener('mouseleave', function () {
            mouse.x = -9999; mouse.y = -9999;
        });

        for (var i = 0; i < COUNT; i++) {
            particles.push({
                x:  Math.random() * canvas.width,
                y:  Math.random() * canvas.height,
                r:  Math.random() * 1.8 + 0.5,
                dx: (Math.random() - 0.5) * 0.4,
                dy: (Math.random() - 0.5) * 0.4,
                o:  Math.random() * 0.45 + 0.1
            });
        }

        function drawCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            var dark = document.documentElement.getAttribute('data-theme') === 'dark';
            var baseColor = dark ? '56,173,248' : '14,145,232';

            // Draw connections
            for (var a = 0; a < particles.length; a++) {
                for (var b = a + 1; b < particles.length; b++) {
                    var dx = particles[a].x - particles[b].x;
                    var dy = particles[a].y - particles[b].y;
                    var dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < CONNECT_DIST) {
                        var alpha = (1 - dist / CONNECT_DIST) * 0.18;
                        ctx.beginPath();
                        ctx.moveTo(particles[a].x, particles[a].y);
                        ctx.lineTo(particles[b].x, particles[b].y);
                        ctx.strokeStyle = 'rgba(' + baseColor + ',' + alpha + ')';
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }
                // Mouse repel
                var mdx = particles[a].x - mouse.x;
                var mdy = particles[a].y - mouse.y;
                var md  = Math.sqrt(mdx * mdx + mdy * mdy);
                if (md < 80) {
                    particles[a].x += mdx / md * 1.5;
                    particles[a].y += mdy / md * 1.5;
                }
            }

            // Draw particles
            particles.forEach(function (p) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(' + baseColor + ',' + p.o + ')';
                ctx.fill();

                p.x += p.dx; p.y += p.dy;
                if (p.x < 0 || p.x > canvas.width)  p.dx *= -1;
                if (p.y < 0 || p.y > canvas.height)  p.dy *= -1;
            });

            requestAnimationFrame(drawCanvas);
        }
        drawCanvas();
    }

    /* ── 5. ENHANCED SCROLL REVEAL (blur + stagger) ─────── */
    (function () {
        var allReveal = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale, .reveal-blur');
        if (!('IntersectionObserver' in window)) {
            allReveal.forEach(function (el) { el.classList.add('visible'); });
            return;
        }
        var obs = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    var delay = el.dataset.delay || 0;
                    setTimeout(function () { el.classList.add('visible'); }, parseFloat(delay) * 1000);
                    obs.unobserve(el);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        allReveal.forEach(function (el) { obs.observe(el); });
    })();

    /* ── 6. MAGNETIC BUTTONS ────────────────────────────── */
    if (window.innerWidth > 768) {
        document.querySelectorAll('.btn-hero-primary, .btn-hero-outline, .btn-cta-white').forEach(function (btn) {
            btn.addEventListener('mousemove', function (e) {
                var rect = btn.getBoundingClientRect();
                var x = e.clientX - rect.left - rect.width  / 2;
                var y = e.clientY - rect.top  - rect.height / 2;
                btn.style.transform = 'translate(' + x * 0.18 + 'px, ' + y * 0.18 + 'px) scale(1.04)';
            });
            btn.addEventListener('mouseleave', function () {
                btn.style.transform = '';
            });
        });
    }

    /* ── 7. 3D TILT ON FEATURE CARDS ───────────────────── */
    if (window.innerWidth > 768) {
        document.querySelectorAll('.feature-card').forEach(function (card) {
            card.addEventListener('mousemove', function (e) {
                var rect = card.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width  - 0.5;
                var y = (e.clientY - rect.top)  / rect.height - 0.5;
                card.style.transform = 'perspective(800px) rotateY(' + (x * 10) + 'deg) rotateX(' + (-y * 8) + 'deg) translateY(-6px)';
            });
            card.addEventListener('mouseleave', function () {
                card.style.transform = '';
            });
        });
    }

    /* ── 8. ACTIVE NAV LINK ON SCROLL ───────────────────── */
    (function () {
        var sections = document.querySelectorAll('section[id]');
        var navLinks = document.querySelectorAll('.nav-link');
        if (!sections.length || !navLinks.length) return;
        var obs = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var id = entry.target.id;
                    navLinks.forEach(function (link) {
                        var href = link.getAttribute('href') || '';
                        link.classList.toggle('active', href === '#' + id);
                    });
                }
            });
        }, { rootMargin: '-40% 0px -40% 0px' });
        sections.forEach(function (s) { obs.observe(s); });
    })();

    /* ── 9. CTA FLOATING PARTICLES ──────────────────────── */
    var ctaSection = document.querySelector('.cta-section');
    if (ctaSection) {
        for (var i = 0; i < 14; i++) {
            (function (i) {
                var p = document.createElement('div');
                p.className = 'cta-particle';
                var size = Math.random() * 60 + 20;
                p.style.cssText = [
                    'width:'  + size + 'px',
                    'height:' + size + 'px',
                    'left:'   + Math.random() * 100 + '%',
                    'bottom:' + (-size) + 'px',
                    'animation-duration:' + (Math.random() * 8 + 6) + 's',
                    'animation-delay:'    + (Math.random() * 6) + 's'
                ].join(';');
                ctaSection.appendChild(p);
            })(i);
        }
    }

    /* ── 10. TYPED HERO HEADLINE WORDS ──────────────────── */
    var typeTarget = document.getElementById('hero-typed-word');
    if (typeTarget) {
        var words = ['Faster', 'Smarter', 'Better', 'Together'];
        var wIdx = 0, cIdx = 0, deleting = false;
        function type() {
            var word = words[wIdx];
            if (!deleting) {
                typeTarget.textContent = word.slice(0, ++cIdx);
                if (cIdx === word.length) { deleting = true; setTimeout(type, 1600); return; }
                setTimeout(type, 80);
            } else {
                typeTarget.textContent = word.slice(0, --cIdx);
                if (cIdx === 0) { deleting = false; wIdx = (wIdx + 1) % words.length; setTimeout(type, 300); return; }
                setTimeout(type, 45);
            }
        }
        type();
    }

    /* ── 11. PLAN CARD HOVER INTERACTION ────────────────── */
    document.querySelectorAll('.plan-card').forEach(function (card) {
        card.addEventListener('mouseenter', function () {
            document.querySelectorAll('.plan-card').forEach(function (c) {
                if (c !== card) c.style.opacity = '0.75';
            });
        });
        card.addEventListener('mouseleave', function () {
            document.querySelectorAll('.plan-card').forEach(function (c) {
                c.style.opacity = '';
            });
        });
    });

    /* ── 12. SMOOTH ANCHOR SCROLL ───────────────────────── */
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
        a.addEventListener('click', function (e) {
            var target = document.querySelector(a.getAttribute('href'));
            if (target) {
                e.preventDefault();
                var top = target.getBoundingClientRect().top + window.scrollY - 70;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        });
    });

})();
