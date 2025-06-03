// Define a datatype for user-response
class UserResponse {
    constructor(id, fleetid, userprompt, responsesql, responsesql_result, responsetext, timestamp) {
        this.id = id;
        this.fleetid = fleetid;
        this.userprompt = userprompt;
        this.responsesql = responsesql;
        this.responsesql_result = responsesql_result; // Assuming this is a JSON string or object
        this.responsetext = responsetext;
        this.timestamp = timestamp;
    }
}

// Sample data
const userResponses = [
    new UserResponse(
        1,
        2,
        "give me the vehicle vin in fleet 1",
        "SELECT vehicles.vin FROM vehicle WHERE vehicle.fleet_id = 2;",
        '[{"vin":"LDN8888"},{"vin":"LDN7777"},{"vin":"LDN9999"}]', // Assuming this is a JSON string representing the result
        "The vehicle VINs in fleet 1 are not available in the current data.",
        "2024-06-02T14:11:00Z"
    ),
    new UserResponse(
        2,
        1,
        "Give me the latest summary of my fleet's daily performance.",
        "SELECT date, total_distance_km, total_energy_kwh, active_vehicles, avg_soc_pct FROM fleet_daily_summary WHERE fleet_id = 1 ORDER BY date DESC LIMIT 1",
        "[{'date': '2025-05-14', 'total_distance_km': 320.0, 'total_energy_kwh': 260.0, 'active_vehicles': 3, 'avg_soc_pct': 60.0}]", // Assuming this is a JSON string representing the result
        "As of May 14, 2025, your fleet traveled a total of 320 km, used 260 kWh of energy, had 3 active vehicles, and an average state of charge of 60%.",
        "2024-06-02T10:21:00Z"
    ),
    new UserResponse(
        3,
        1,
        "tell me the maintenance log of my vehicles",
        "SELECT * FROM maintenance_logs WHERE vehicle_id IN (SELECT vehicle_id FROM vehicles WHERE fleet_id = 1)",
        '[{"maint_id":1,"vehicle_id":3,"maint_type":"BMS Update","start_ts":"2025-04-29T12:00:00+00:00","end_ts":"2025-04-30T12:00:00+00:00","cost_sgd":800,"notes":"Firmware"},{"maint_id":3,"vehicle_id":1,"maint_type":"Brake Inspection","start_ts":"2025-05-07T12:00:00+00:00","end_ts":"2025-05-07T14:00:00+00:00","cost_sgd":300,"notes":"Passed"}]', // Assuming this is a JSON string representing the result
        "Here are the maintenance logs for your vehicles in fleet 1:\
- Vehicle 3: BMS Update on April 29-30, 2025, costing SGD 800. Notes: Firmware update.\
- Vehicle 1: Brake Inspection on May 7, 2025, costing SGD 300. Notes: Passed inspection.",
        "2024-06-02T11:31:00Z"
    ),
    new UserResponse(
        4,
        1,
        "example How many SRM T3 EVs are in the fleet?",
        "SELECT COUNT(*) FROM vehicles WHERE fleet_id = 1 AND model = 'SRM T3';",
        '[{"count": 2}]', // Assuming this is a JSON string representing the result
        "You have 2 SRM T3 EVs in your fleet.",
        "2024-06-10T10:30:00Z"
    ),
    new UserResponse(
        5,
        1,
        "example What is the total distance traveled by all vehicles?",
        "SELECT SUM(distance) FROM vehicle_data;",
        '[{"total_distance": 15000}]', // Assuming this is a JSON string representing the result
        "The total distance traveled by all vehicles is 15,000 km.",
        "2024-06-10T10:35:00Z"
    )
];

token = {
    1: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6MX0.DLzkE0mnFbNTEN1MPcBC7ywxZxVtDPYe23oasblELn0',
    2: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6Mn0.7eMYokNtpIbVrVQjL6xP3_bYqJbkO4cOqxKb29T1eNw',
    3: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6M30.4uZe5wr4BRbJbF-V9mW3-HFBnzhlIOG37tpXL8HpnnI'
}

const form = document.getElementById('chat-form');
const queryInput = document.getElementById('query');
const responseBox = document.getElementById('response-box');
const historyContainer = document.getElementById('history-container');

const chatHistory = [];

// Load sample data into history
userResponses.forEach(userResponse => {
    chatHistory.push(userResponse);
    addHistoryCard(userResponse);
});

form.addEventListener('submit', async (e) => {
    const fleetid = document.getElementById('fleet-select');
    if (queryInput.value.trim() === "") {
        alert("Please enter a query.");
        return;
    }
    if (fleetid.value === "") {
        alert("Please select a fleet.");
        return;
    }

    e.preventDefault();
    // disable submit button
    form.querySelector('button[type="submit"]').disabled = true;
    const query = queryInput.value;
    responseBox.style.display = "block";
    responseBox.innerText = "Processing...";

    const res = await fetch("/chat", {
    method: "POST",
    headers: {
        "Authorization": "Bearer " + token[fleetid.value], // Use the selected fleet's token
        "Content-Type": "application/json"
    },
    body: JSON.stringify({ query })
    });``

    const answer = await res.text();
    sql = JSON.parse(answer).sql;
    sql_results = JSON.parse(answer).raw_results;
    humanReadableText = JSON.parse(answer).human_readable_text;

    responseBox.innerHTML = humanReadableText; // answer is in JSON format.

    // Save to history
    const timestamp = new Date().toISOString(); // example timestamp format: "2024-06-10T10:15:00Z"
    const userResponse = new UserResponse(
        chatHistory.length + 1, // Incremental ID
        fleetid.value, // Use the selected fleet ID
        query,
        sql,
        JSON.stringify(sql_results), // Convert results to JSON string
        humanReadableText,
        timestamp
    );
    chatHistory.push(userResponse);
    addHistoryCard(userResponse);

    queryInput.value = "";
    form.querySelector('button[type="submit"]').disabled = false;
});

function addHistoryCard(userResponse) {
    const card = document.createElement("div");

    split_date =  userResponse.timestamp.split("T");
    const [year, month, day] = split_date[0].split("-");
    date = `${day}-${month}-${year}`;
    time = split_date[1].split(":")[0] + split_date[1].split(":")[1]; // "10:15:00"

    card.className = "history-card";
    card.innerHTML = `
        <table class="history-table">
            <colgroup>
                <col style="min-width: 110px;">
                <col>
            </colgroup>
            <tr>
                <td><strong>Prompt:</strong></td>
                <td><b>${userResponse.userprompt}</b></td>
            </tr>
            <tr>
                <td><strong>SQL:</strong></td>
                <td style="color: var(--sunset-yellow) !important;"><code>${userResponse.responsesql}</code></td>
            </tr>
            <tr>
                <td><strong>SQL Result:</strong></td>
                <td>${userResponse.responsesql_result}</td>
            </tr>
            <tr>
                <td><strong>Text Response:</strong></td>
                <td>${userResponse.responsetext}</td>
            </tr>
        </table>
        <div style="text-align: right; font-size: 0.8em; margin-top: 4px;">
            <i>${date} | ${time} | fleetid: ${userResponse.fleetid}</i>
        </div>
    `;
    historyContainer.appendChild(card);
}

// Make cards draggable with SortableJS
new Sortable(historyContainer, {
    animation: 150,
    ghostClass: 'dragging'
});