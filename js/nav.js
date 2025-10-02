const hamburger = document.querySelector('.hamburger');
const navUl = document.querySelector('.nav-links ul');

hamburger?.addEventListener('click', () => {
  navUl.classList.toggle('show');
});
