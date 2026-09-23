// ── Screen switching ────────────────────────────
  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('screen-' + id).classList.add('active');

    document.querySelectorAll('.nav-item').forEach((btn, i) => {
      btn.classList.remove('active');
      if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes("'" + id + "'")) {
        btn.classList.add('active');
      }
    });

    // close sidenav on mobile
    if (window.innerWidth <= 520) {
      document.getElementById('sidenav').classList.remove('open');
    }
  }

  // ── Side nav toggle ─────────────────────────────
  function toggleNav() {
    document.getElementById('sidenav').classList.toggle('open');
  }

  // ── Auth tab switching ──────────────────────────
  function switchAuthTab(mode) {
    const isSignup = mode === 'signup';
    document.getElementById('tab-login').classList.toggle('active', !isSignup);
    document.getElementById('tab-signup').classList.toggle('active', isSignup);
    document.getElementById('signup-name').style.display = isSignup ? 'block' : 'none';
    document.getElementById('signup-confirm').style.display = isSignup ? 'block' : 'none';
    document.getElementById('forgot-btn').style.display = isSignup ? 'none' : 'block';
    document.getElementById('login-title').textContent = isSignup ? 'অ্যাকাউন্ট তৈরি করুন 🎉' : 'স্বাগতম 👋';
    document.getElementById('login-subtitle').textContent = isSignup
      ? 'HELPNET-এ যোগ দিন এবং পরিবর্তন আনুন'
      : 'আপনার সম্প্রদায়কে সাহায্য করতে সাইন ইন করুন';
    document.getElementById('auth-main-btn').textContent = isSignup ? 'অ্যাকাউন্ট তৈরি করুন' : 'সাইন ইন';
  }

  // ── Generic tab switcher ────────────────────────
  function switchTab(prefix, id, btn) {
    // Update buttons
    btn.closest('.tab-row').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Show/hide tab content
    ['users','reports','posts','upcoming','myevents'].forEach(tab => {
      const el = document.getElementById(prefix + '-tab-' + tab);
      if (el) el.style.display = (tab === id) ? 'block' : 'none';
    });
  }

  // ── Blood filter chips ──────────────────────────
  function setBloodFilter(btn, group) {
    document.querySelectorAll('#blood-filter .chip-btn').forEach(b => {
      b.className = 'chip-btn off';
      b.style.background = '';
      b.style.color = '';
      b.style.boxShadow = '';
    });
    btn.className = 'chip-btn tag-active';
    btn.style.background = 'linear-gradient(145deg,#e63946,#c1121f)';
    btn.style.boxShadow = '3px 3px 8px rgba(230,57,70,0.3)';
    btn.style.color = '#fff';
  }