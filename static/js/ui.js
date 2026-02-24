document.addEventListener("DOMContentLoaded", () => {
  // Trigger reveal animations
  const reveals = document.querySelectorAll(".reveal");
  
  reveals.forEach((el, i) => {
    setTimeout(() => {
      el.classList.add("active");
    }, i * 150); // Staggers the animation if there are multiple cards
  });
});