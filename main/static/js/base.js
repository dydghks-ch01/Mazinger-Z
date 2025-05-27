const navIcon = document.getElementById('navIcon');
const wrapper = document.querySelector('.wrapper');
const menuLinks = document.querySelectorAll('.side-menu li');

navIcon.addEventListener('click', () => {
  wrapper.classList.toggle('nav-open');
});

menuLinks.forEach(link => {
  link.addEventListener('click', () => {
    const targetId = link.getAttribute('data-target');
    document.getElementById(targetId).scrollIntoView({ behavior: 'smooth' });
    wrapper.classList.remove('nav-open');
  });
});

document.addEventListener('click', (event) => {
  const isMenuOpen = wrapper.classList.contains('nav-open');
  const isNavIcon = event.target.closest('#navIcon');
  const isSideMenu = event.target.closest('.side-menu');
  if (isMenuOpen && !isNavIcon && !isSideMenu) {
    wrapper.classList.remove('nav-open');
  }
});


document.addEventListener("DOMContentLoaded", () => {
  const $filter = document.querySelector('.svg-sprite');
  if (!$filter) return;
  const $turb = $filter.querySelector('#filter feTurbulence');
  const turbVal = { val: 0.000001 };
  const turbValX = { val: 0.000001 };

  const glitchTimeline = () => {
    const timeline = gsap.timeline({
      repeat: -1,
      repeatDelay: 2,
      paused: true,
      onUpdate: () => {
        $turb.setAttribute('baseFrequency', turbVal.val + ' ' + turbValX.val);
      }
    });

    timeline
      .to(turbValX, { val: 0.5, duration: 0.1 })
      .to(turbVal, { val: 0.02, duration: 0.1 })
      .set(turbValX, { val: 0.000001 })
      .set(turbVal, { val: 0.000001 })
      .to(turbValX, { val: 0.4, duration: 0.2 }, 0.4)
      .to(turbVal, { val: 0.002, duration: 0.2 }, 0.4)
      .set(turbValX, { val: 0.000001 })
      .set(turbVal, { val: 0.000001 });

    return {
      start: () => timeline.play(0),
      stop: () => timeline.pause()
    };
  };

  const btnGlitch = glitchTimeline();

  document.querySelectorAll('.btn-glitch').forEach(button => {
    button.addEventListener('mouseenter', () => {
      button.classList.add('btn-glitch-active');
      btnGlitch.start();
    });
    button.addEventListener('mouseleave', () => {
      button.classList.remove('btn-glitch-active');
      btnGlitch.stop();
    });
  });
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      window.location.reload();
    }
  });
});
