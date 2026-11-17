const D = JSON.parse(document.getElementById("chartData").textContent);
const C = {Kritik:"#dc3545", Yuqori:"#fd7e14", "O‘rta":"#0dcaf0", Past:"#198754", "Muvaffaqiyatli":"#198754", Xatolik:"#dc3545",
  Kutilmoqda:"#6c757d", "Tekshirish kerak":"#ffc107", Mos:"#198754", "Qisman mos":"#ffc107", "Mos emas":"#dc3545", "Tegishli emas":"#6c757d"};
const col = l => l.map(x => C[x] || "#0d6efd");
const mk = (id, type, d, extra = {}) => new Chart(document.getElementById(id), {type,
  data: {labels: d.labels, datasets: [{data: d.data, backgroundColor: type === "bar" ? col(d.labels) : col(d.labels), borderWidth: 1}]},
  options: Object.assign({responsive: true, plugins: {legend: {display: type !== "bar", position: "bottom"}}}, extra)});
mk("cRisk", "doughnut", D.risk); mk("cAudit", "pie", D.audit); mk("cBackup", "doughnut", D.backup);
mk("cInc", "bar", D.incident, {scales: {y: {beginAtZero: true, ticks: {precision: 0}}}});
new Chart(document.getElementById("cReady"), {type: "bar", data: {labels: D.ready.labels, datasets: [{data: D.ready.data, backgroundColor: ["#0d6efd", "#06b6d4"]}]},
  options: {indexAxis: "y", plugins: {legend: {display: false}}, scales: {x: {min: 0, max: 100}}}});
