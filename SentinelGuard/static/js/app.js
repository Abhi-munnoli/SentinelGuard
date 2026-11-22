document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("fraudChart");
  if (canvas && window.sgChartData && window.Chart) {
    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Predicted genuine", "Predicted fraud"],
        datasets: [{ data: [window.sgChartData.genuine, window.sgChartData.fraud] }]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } }, cutout: "68%" }
    });
  }
});
