document.addEventListener('DOMContentLoaded', function() {
    let clientLat = null;
    let clientLon = null;
    let map = null;
    let markers = [];

    // Try to get client location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            clientLat = position.coords.latitude;
            clientLon = position.coords.longitude;
        }, function() {
            showError('Location access denied. Please allow location access for accurate results.');
        });
    } else {
        showError('Geolocation is not supported by this browser.');
    }

    // Load options for selects
    fetch('/options')
        .then(res => res.json())
        .then(data => {
            fillSelect('location', data.locations);
            fillSelect('work_type', data.work_types);
            fillSelect('time_slot', data.time_slots);
            fillSelect('language', ['Any', ...data.languages]);
        });

    function fillSelect(id, options) {
        const select = document.getElementById(id);
        select.innerHTML = '';
        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            select.appendChild(option);
        });
    }

    document.getElementById('plumberForm').addEventListener('submit', function(e) {
        e.preventDefault();
        if (clientLat === null || clientLon === null) {
            showError('Waiting for your location. Please allow location access and try again.');
            return;
        }
        const form = e.target;
        const data = {
            location: form.location.value,
            work_type: form.work_type.value,
            time_slot: form.time_slot.value,
            language: form.language.value,
            client_lat: clientLat,
            client_lon: clientLon
        };
        showLoading();
        fetch('/find_plumbers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(data => {
            showResults(data.plumbers);
            showMap(data.plumbers);
        })
        .catch(() => showError('An error occurred. Please try again.'));
    });

    function showLoading() {
        document.getElementById('results').innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p>Searching for plumbers...</p></div>';
        if (map) map.remove();
    }

    function showResults(plumbers) {
        if (!plumbers.length) {
            document.getElementById('results').innerHTML = '<div class="alert alert-warning text-center">No plumbers found matching your criteria.</div>';
            if (map) map.remove();
            return;
        }
        let html = '<table class="table table-bordered table-hover"><thead><tr>' +
            '<th>Name</th><th>District</th><th>Specialization</th><th>Free Time Slots</th><th>Languages</th><th>Distance (km)</th><th>ETA (min)</th>' +
            '</tr></thead><tbody>';
        plumbers.forEach(p => {
            html += `<tr><td>${p.Name}</td><td>${p.District}</td><td>${p.Work_Specialization}</td><td>${p.Free_Time_Slots}</td><td>${p.Languages_Spoken}</td><td>${p.Distance_km}</td><td>${p.ETA_min}</td></tr>`;
        });
        html += '</tbody></table>';
        document.getElementById('results').innerHTML = html;
    }

    function showMap(plumbers) {
        if (map) map.remove();
        map = L.map('map').setView([clientLat, clientLon], 8);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        // Client marker (blue)
        const clientMarker = L.marker([clientLat, clientLon], {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            })
        }).addTo(map).bindPopup('You (Client)').openPopup();
        markers = [clientMarker];
        // Plumber markers (red)
        plumbers.forEach(p => {
            const plumberMarker = L.marker([p.Latitude, p.Longitude], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                })
            }).addTo(map).bindPopup(`<b>${p.Name}</b><br>${p.District}<br>Distance: ${p.Distance_km} km<br>ETA: ${p.ETA_min} min`);
            markers.push(plumberMarker);
        });
        // Fit map to all markers
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.2));
    }

    function showError(msg) {
        document.getElementById('results').innerHTML = `<div class="alert alert-danger text-center">${msg}</div>`;
        if (map) map.remove();
    }
}); 