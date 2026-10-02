/* AI Hospital — Beautiful Animated Background */
(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let width, height, particles = [];
  const PARTICLE_COUNT = 70;

  const colors = [
    "rgba(44, 127, 184, 0.35)",
    "rgba(10, 75, 122, 0.28)",
    "rgba(243, 156, 18, 0.18)",
    "rgba(255, 255, 255, 0.55)",
    "rgba(190, 230, 255, 0.45)",
    "rgba(120, 200, 240, 0.30)",
  ];

  function initParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 60 + 20,
        color: colors[Math.floor(Math.random() * colors.length)],
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.25,
      });
    }
  }

  function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    initParticles();
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, "#d4eafc");
    gradient.addColorStop(0.5, "#e8f4fe");
    gradient.addColorStop(1, "#f0f9ff");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < -p.radius) p.x = width + p.radius;
      if (p.x > width + p.radius) p.x = -p.radius;
      if (p.y < -p.radius) p.y = height + p.radius;
      if (p.y > height + p.radius) p.y = -p.radius;

      const radGrad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
      radGrad.addColorStop(0, p.color);
      radGrad.addColorStop(1, "rgba(255, 255, 255, 0)");

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = radGrad;
      ctx.fill();
    });

    for (let i = 0; i < 40; i++) {
      const x = (i * 131 + Date.now() * 0.01) % width;
      const y = (i * 237) % height;
      const alpha = 0.4 + 0.3 * Math.sin(Date.now() * 0.002 + i);
      ctx.beginPath();
      ctx.arc(x, y, 1.4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.fill();
    }

    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();
  draw();
})();