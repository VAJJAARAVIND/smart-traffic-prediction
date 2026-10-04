
import { useEffect, useState } from "react";
import {
  Activity,
  CarFront,
  Gauge,
  MapPin,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Clock3,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
const COLORS = ["#22c55e", "#f59e0b", "#ef4444"];

function App() {
  const [summary, setSummary] = useState(null);
  const [roads, setRoads] = useState([]);
  const [hourly, setHourly] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    Vehicle_Count: 400,
    Average_Speed: 30,
    Hour: 18,
    Location: "Road A",
    Weather: "Clear",
    Road_Condition: "Good",
  });

  const [prediction, setPrediction] = useState(null);
  const [predictError, setPredictError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const endpoints = [
        "/api/summary",
        "/api/roads",
        "/api/hourly",
        "/api/model-metrics",
      ];

      const responses = await Promise.all(
        endpoints.map((endpoint) =>
          fetch(`${API}${endpoint}`)
        )
      );

      if (responses.some((response) => !response.ok)) {
        throw new Error("Could not load dashboard data.");
      }

      const [s, r, h, m] = await Promise.all(
        responses.map((response) => response.json())
      );

      setSummary(s);
      setRoads(r);
      setHourly(h);
      setMetrics(m);
    } catch (err) {
      setError(
        "Unable to connect to Flask. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function predictTraffic(event) {
    event.preventDefault();
    setPrediction(null);
    setPredictError("");

    try {
      const response = await fetch(`${API}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          Vehicle_Count: Number(form.Vehicle_Count),
          Average_Speed: Number(form.Average_Speed),
          Hour: Number(form.Hour),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Prediction failed.");
      }

      setPrediction(data);
    } catch (err) {
      setPredictError(err.message);
    }
  }

  const distribution = summary
    ? Object.entries(summary.traffic_distribution).map(
        ([name, value]) => ({ name, value })
      )
    : [];

  const field = (name, label, options) => (
    <label className="field" key={name}>
      <span>{label}</span>
      {options ? (
        <select
          value={form[name]}
          onChange={(e) =>
            setForm({ ...form, [name]: e.target.value })
          }
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : (
        <input
          type="number"
          value={form[name]}
          min={name === "Hour" ? 0 : 0}
          max={
            name === "Hour"
              ? 23
              : name === "Average_Speed"
              ? 200
              : 100000
          }
          required
          onChange={(e) =>
            setForm({ ...form, [name]: e.target.value })
          }
        />
      )}
    </label>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Activity /></div>
          <div>
            <h2>TrafficIQ</h2>
            <small>Intelligent Mobility</small>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">
          <Activity size={18} /> Overview
        </div>
        <div className="nav-item">
          <MapPin size={18} /> Road Analytics
        </div>
        <div className="nav-item">
          <TrendingUp size={18} /> Predictions
        </div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>API connection</strong>
            <small>Local Flask server</small>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">INTELLIGENT TRANSPORTATION SYSTEM</div>
            <h1>Traffic Monitoring Dashboard</h1>
            <p>Analyze road conditions and predict traffic congestion.</p>
          </div>
          <button className="refresh-btn" onClick={loadDashboard}>
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        {error && <div className="error-banner">{error}</div>}
        {loading && <p className="loading">Loading traffic analytics...</p>}

        {summary && (
          <>
            <section className="metrics-grid">
              <Metric
                icon={<CarFront />}
                label="Vehicles Recorded"
                value={summary.total_vehicles.toLocaleString()}
                note={`${summary.total_records.toLocaleString()} dataset records`}
                color="blue"
              />
              <Metric
                icon={<Gauge />}
                label="Average Speed"
                value={`${summary.average_speed} km/h`}
                note="Across all recorded roads"
                color="green"
              />
              <Metric
                icon={<Clock3 />}
                label="Peak Traffic Hour"
                value={`${summary.busiest_hour}:00`}
                note="Highest average vehicle count"
                color="orange"
              />
              <Metric
                icon={<AlertTriangle />}
                label="Busiest Road"
                value={summary.busiest_road}
                note="By total recorded vehicles"
                color="red"
              />
            </section>

            <section className="charts-grid">
              <div className="panel wide-panel">
                <PanelTitle
                  title="Hourly Traffic Trends"
                  subtitle="Average vehicle count by hour"
                />
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={hourly}>
                    <defs>
                      <linearGradient id="trafficFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#263244" strokeDasharray="3 3" />
                    <XAxis dataKey="Hour" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: "#111c2e", border: "1px solid #334155", borderRadius: 10 }} />
                    <Area
                      type="monotone"
                      dataKey="Average_Vehicles"
                      name="Average vehicles"
                      stroke="#38bdf8"
                      fill="url(#trafficFill)"
                      strokeWidth={3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="panel">
                <PanelTitle
                  title="Traffic Distribution"
                  subtitle="Dataset classification"
                />
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={distribution}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={58}
                      outerRadius={85}
                      paddingAngle={4}
                    >
                      {distribution.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={
                            COLORS[
                              ["Low", "Medium", "High"].indexOf(entry.name)
                            ] || COLORS[index % COLORS.length]
                          }
                        />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#111c2e", border: "1px solid #334155", borderRadius: 10 }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="bottom-grid">
              <div className="panel">
                <PanelTitle
                  title="Road Performance"
                  subtitle="Vehicle volume and average speed"
                />
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={roads}>
                    <CartesianGrid stroke="#263244" strokeDasharray="3 3" />
                    <XAxis dataKey="Location" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: "#111c2e", border: "1px solid #334155", borderRadius: 10 }} />
                    <Bar
                      dataKey="Average_Vehicles"
                      name="Avg. vehicles"
                      fill="#818cf8"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Road</th>
                        <th>Avg. vehicles</th>
                        <th>Avg. speed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {roads.map((road) => (
                        <tr key={road.Location}>
                          <td>{road.Location}</td>
                          <td>{Number(road.Average_Vehicles).toFixed(1)}</td>
                          <td>{Number(road.Average_Speed).toFixed(1)} km/h</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="panel prediction-panel">
                <PanelTitle
                  title="Traffic Prediction"
                  subtitle="Use the trained ML model"
                />
                <form onSubmit={predictTraffic}>
                  <div className="form-grid">
                    {field("Vehicle_Count", "Vehicle count")}
                    {field("Average_Speed", "Average speed (km/h)")}
                    {field("Hour", "Hour (0–23)")}
                    {field("Location", "Road", ["Road A", "Road B", "Road C", "Road D", "Road E"])}
                    {field("Weather", "Weather", ["Clear", "Cloudy", "Rainy", "Foggy"])}
                    {field("Road_Condition", "Road condition", ["Good", "Moderate", "Poor"])}
                  </div>
                  <button className="predict-btn" type="submit">
                    <TrendingUp size={17} /> Predict Traffic Level
                  </button>
                </form>

                {predictError && (
                  <div className="error-banner">{predictError}</div>
                )}

                {prediction && (
                  <div className={`prediction-result ${prediction.predicted_traffic_level.toLowerCase()}`}>
                    <small>MODEL PREDICTION</small>
                    <h2>{prediction.predicted_traffic_level} Traffic</h2>
                    <p>Model confidence: {prediction.confidence_percent}%</p>
                    <div className="probability-list">
                      {Object.entries(prediction.probabilities).map(([name, value]) => (
                        <div className="probability-row" key={name}>
                          <span>{name}</span>
                          <div className="probability-track">
                            <div
                              className="probability-fill"
                              style={{ width: `${value}%` }}
                            />
                          </div>
                          <strong>{value}%</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {metrics && (
                  <div className="model-note">
                    <span>Random Forest model</span>
                    <strong>{(metrics.accuracy * 100).toFixed(2)}% test accuracy</strong>
                  </div>
                )}
              </div>
            </section>

            <footer>
              TrafficIQ · Smart Traffic Prediction & Monitoring System
              <span>Prototype using synthetic traffic data</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

function Metric({ icon, label, value, note, color }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${color}`}>{icon}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </div>
  );
}

function PanelTitle({ title, subtitle }) {
  return (
    <div className="panel-title">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

export default App;