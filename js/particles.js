(function () {
  const canvas = document.getElementById('world-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const palette = [
    [45, 212, 191],
    [86, 216, 255],
    [139, 92, 246],
    [200, 166, 75],
  ];

  let width = 0;
  let height = 0;
  let dpr = 1;
  let t = 0;
  let points = [];
  let raf = null;
  let pointer = { x: -999, y: -999 };

  function resize() {
    const rect = canvas.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(width * dpr));
    canvas.height = Math.max(1, Math.floor(height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    buildPoints();
  }

  function buildPoints() {
    const target = width < 760 ? 46 : width < 1100 ? 68 : 92;
    points = [];
    for (let i = 0; i < target; i += 1) {
      const band = i % 4;
      const color = palette[band];
      points.push({
        x: Math.random() * width,
        y: Math.random() * height,
        ox: Math.random() * Math.PI * 2,
        oy: Math.random() * Math.PI * 2,
        speed: 0.003 + Math.random() * 0.004,
        radius: 1.4 + Math.random() * 2.6,
        color: color,
        band: band,
      });
    }
  }

  function clear() {
    ctx.clearRect(0, 0, width, height);
  }

  function drawBackground() {
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, 'rgba(7, 11, 20, 0.1)');
    gradient.addColorStop(1, 'rgba(13, 20, 35, 0.28)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    ctx.save();
    ctx.globalAlpha = 0.16;
    ctx.strokeStyle = 'rgba(86, 216, 255, 0.26)';
    ctx.lineWidth = 1;
    const step = width < 760 ? 72 : 94;
    for (let x = (t * 0.08) % step; x < width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x - height * 0.18, height);
      ctx.stroke();
    }
    for (let y = (t * 0.05) % step; y < height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y + width * 0.07);
      ctx.stroke();
    }
    ctx.restore();
  }

  function pointPosition(point) {
    const driftX = Math.sin(t * point.speed + point.ox) * 28;
    const driftY = Math.cos(t * point.speed * 1.3 + point.oy) * 22;
    return {
      x: point.x + driftX,
      y: point.y + driftY,
    };
  }

  function drawConnections(positions) {
    for (let i = 0; i < positions.length; i += 1) {
      const a = positions[i];
      for (let j = i + 1; j < positions.length; j += 1) {
        const b = positions[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const limit = a.band === b.band ? 142 : 96;
        if (dist < limit) {
          const alpha = (1 - dist / limit) * (a.band === b.band ? 0.18 : 0.08);
          ctx.strokeStyle = `rgba(86, 216, 255, ${alpha})`;
          ctx.lineWidth = a.band === b.band ? 0.9 : 0.55;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }
  }

  function drawPointerField(positions) {
    if (pointer.x < 0 || pointer.y < 0) return;
    const radius = 170;
    positions.forEach(function (p) {
      const dx = p.x - pointer.x;
      const dy = p.y - pointer.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < radius) {
        const alpha = (1 - dist / radius) * 0.32;
        ctx.strokeStyle = `rgba(200, 166, 75, ${alpha})`;
        ctx.lineWidth = 1.1;
        ctx.beginPath();
        ctx.moveTo(pointer.x, pointer.y);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
      }
    });
  }

  function drawPoints(positions) {
    positions.forEach(function (p) {
      const [r, g, b] = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.72)`;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius * 4.2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.045)`;
      ctx.fill();
    });
  }

  function drawMechanismPaths() {
    ctx.save();
    ctx.globalAlpha = 0.62;
    for (let i = 0; i < 3; i += 1) {
      const yBase = height * (0.25 + i * 0.18);
      ctx.strokeStyle = i === 1 ? 'rgba(45, 212, 191, 0.18)' : 'rgba(139, 92, 246, 0.14)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (let x = -30; x <= width + 30; x += 18) {
        const y = yBase + Math.sin(x * 0.011 + t * 0.012 + i * 1.7) * 18;
        if (x === -30) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function draw() {
    t += prefersReducedMotion ? 0 : 1;
    clear();
    drawBackground();
    drawMechanismPaths();
    const positions = points.map(function (point) {
      return Object.assign({}, point, pointPosition(point));
    });
    drawConnections(positions);
    drawPointerField(positions);
    drawPoints(positions);

    if (!prefersReducedMotion) {
      raf = requestAnimationFrame(draw);
    }
  }

  window.addEventListener('resize', resize);
  canvas.parentElement.addEventListener('mousemove', function (event) {
    const rect = canvas.parentElement.getBoundingClientRect();
    pointer.x = event.clientX - rect.left;
    pointer.y = event.clientY - rect.top;
  });
  canvas.parentElement.addEventListener('mouseleave', function () {
    pointer.x = -999;
    pointer.y = -999;
  });

  resize();
  draw();

  window.addEventListener('beforeunload', function () {
    if (raf) cancelAnimationFrame(raf);
  });
})();
