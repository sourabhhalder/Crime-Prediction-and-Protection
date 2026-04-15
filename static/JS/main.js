// ---------------- MAP INIT ----------------
let map = L.map('map').setView([25.4358, 81.8463], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
.addTo(map);

let marker;
let heatLayer;
let chart;

// ---------------- FORM SUBMIT ----------------
document.getElementById("form").addEventListener("submit", function(e){
    e.preventDefault();

    const data = {
        locality: document.getElementById("locality").value,
        gender: document.getElementById("gender").value,
        time: document.getElementById("time").value
    };

    fetch("/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(data => {

        // ---------------- RESULT ----------------
        document.getElementById("result").innerHTML = `
            <h3>Safety Score: ${data.safety_score}%</h3>
            <p>${data.message}</p>
            <p><b>Confidence:</b> ${data.confidence}%</p>
            <p><b>Reasons:</b> ${data.reasons.join(", ")}</p>
            <p><b>Nearest Police Station:</b> ${data.police_station}</p>
            <p><b>Safety Advice:</b> ${data.advice.join(", ")}</p>
        `;

        // ---------------- MAP MARKER ----------------
        if (marker) map.removeLayer(marker);

        marker = L.marker([data.lat, data.lon])
            .addTo(map)
            .bindPopup("Selected Area")
            .openPopup();

        map.setView([data.lat, data.lon], 13);

        // ---------------- HEATMAP ----------------
        if (heatLayer) map.removeLayer(heatLayer);

        heatLayer = L.heatLayer(data.heatmap, {
            radius: 25,
            blur: 15
        }).addTo(map);

        // ---------------- CHART ----------------
        if (chart) chart.destroy();

        chart = new Chart(document.getElementById("chart"), {
            type: "line",
            data: {
                labels: data.forecast.map(d => d.day),
                datasets: [{
                    label: "Safety Forecast",
                    data: data.forecast.map(d => d.score),
                    fill: false
                }]
            }
        });

    })
    .catch(err => {
        console.error(err);
        alert("Backend not responding ❌");
let color = data.safety_score > 70 ? "lightgreen" :
            data.safety_score > 40 ? "orange" : "red";

document.getElementById("result").innerHTML = `
    <h3 style="color:${color}">Safety Score: ${data.safety_score}%</h3>
    ...
`;
    });
});