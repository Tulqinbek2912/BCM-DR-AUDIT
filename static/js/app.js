document.addEventListener("DOMContentLoaded", () => {
  const b = document.getElementById("menuBtn"), s = document.getElementById("sidebar");
  if (b) b.addEventListener("click", () => s.classList.toggle("open"));
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => new bootstrap.Popover(el));
  document.querySelectorAll(".step-chk").forEach(cb => cb.addEventListener("change", async () => {
    const token = document.querySelector("#stepForm [name=csrfmiddlewaretoken]").value;
    try {
      const r = await fetch(cb.dataset.url, {method: "POST", headers: {"X-CSRFToken": token}});
      if (!r.ok) throw new Error();
      const d = await r.json();
      cb.nextElementSibling.classList.toggle("text-decoration-line-through", d.done);
      cb.nextElementSibling.classList.toggle("text-muted", d.done);
      const p = document.getElementById("prog"); p.style.width = d.percent + "%"; p.textContent = d.percent + "%";
    } catch (e) { cb.checked = !cb.checked; alert("Saqlashda xatolik yuz berdi."); }
  }));
  document.querySelectorAll(".alert-success").forEach(a => setTimeout(() => a.classList.remove("show"), 5000));
});
