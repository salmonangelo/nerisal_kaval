# CrowdCare (Nerisal Kaval)

Nerisal Kaval (CrowdCare) is a modular, AI-powered crowd risk monitoring system designed for real-time spatial analysis and safety management.

## 🚀 Key Features

- **Multi-Camera Integration**: Scalable pipeline for monitoring multiple zones simultaneously.
- **Improved Frame Sampling**: Optimized at **1Hz** (1 frame per second) for a balance between real-time responsiveness and CPU stability.
- **Intelligent Risk Assessment**: 
    - **Global Density**: Overall crowd levels per zone.
    - **Cluster Detection**: Identifies local hotspots or dangerous crowd groupings via spatial heatmap analysis.
- **Zone Flow Tracking**: Real-time monitoring of people movement between zones with aggregated flow counts.
- **Dynamic Dashboard**: 
    - Glassmorphic UI with real-time intelligence cards.
    - Live MJPEG streams with heatmap and tracking overlays.
    - Detailed per-zone metrics (Count, Density Ratio, Risk Classification, Hotspot Coordinates).
- **Proactive Alerting**: Multi-tier alert system (Amber/Warning, Red/Critical) with cluster-aware notifications.
- **Flexible CLI**: Enhanced `run.py` supporting dynamic video sources or webcam indices.

## 🛠 Project Structure

- **`app/`**: Core logic including detection (YOLOv8), tracking, risk engine, and alert manager.
- **`dashboard/`**: Premium web interface built with Vanilla JS, Chart.js, and CSS.
- **`run.py`**: The primary entry point for the detection/tracking pipeline.
- **`metrics.db`**: Local SQLite persistence for historical safety analytics.

## 🏁 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Run the Detection Loop**:
   
   **Default** (uses webcam 0 for both zones):
   ```bash
   python run.py
   ```
   
   **With independent video sources** (multi-camera):
   ```bash
   python run.py --sourceA 0 --sourceB 1
   ```
   
   **With video files**:
   ```bash
   python run.py --sourceA data/video1.mp4 --sourceB data/video2.mp4
   ```
   
   **Single webcam for both zones** (fallback):
   ```bash
   python run.py --sourceA 0 --sourceB 0
   ```

4. **Access the Command Center**:
   Open your browser and navigate to: [http://localhost:8000/](http://localhost:8000/)

## � Dashboard Gallery

### **Real-Time Monitoring Interface**
Nerisal Kaval provides a professional, glassmorphic dashboard with real-time crowd intelligence:

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203055.png" width="400" alt="Dashboard Overview">
        <br><b>Dashboard Overview</b><br><i>Real-time intelligence cards & metrics</i>
      </td>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203120.png" width="400" alt="Camera Feeds">
        <br><b>Live Camera Feeds</b><br><i>Multi-zone MJPEG streaming with overlays</i>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203131.png" width="400" alt="Zone Intelligence">
        <br><b>Zone Intelligence</b><br><i>Per-zone metrics & risk assessment</i>
      </td>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203205.png" width="400" alt="Density Heatmap">
        <br><b>Density Heatmap</b><br><i>Gaussian-smoothed crowd distribution</i>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203215.png" width="400" alt="Zone Flow Tracking">
        <br><b>Zone Flow Tracking</b><br><i>People movement between zones</i>
      </td>
      <td align="center">
        <img src="screenshot/Screenshot 2026-04-16 203225.png" width="400" alt="Analytics & Alerts">
        <br><b>Analytics & Alerts</b><br><i>Historical trends & critical notifications</i>
      </td>
    </tr>
  </table>
</div>

### **Key Dashboard Features**
- 🎨 **Glassmorphic Design** — Modern, responsive UI with dark/light theme toggle
- 📊 **Real-Time Charts** — Live crowd trends & density distribution graphs
- 🚨 **Alert System** — Multi-tier (Amber/Red) notifications with cluster detection
- 🔄 **Zone Flow Visualization** — Track people movement between monitored zones
- 📈 **Analytics Dashboard** — Historical data, growth rates, density classification
- 🎯 **Hotspot Detection** — Identifies dangerous crowd groupings with coordinates
- 🌍 **Multi-Zone Support** — Independent monitoring of separate camera feeds

## �🔧 Configuration

Global settings such as thresholds and sampling rates can be modified in `app/config.py`. 

| Setting | Description | Default |
|---------|-------------|---------|
| `FRAME_INTERVAL_SECONDS` | Delay between sampled frames | `1.0` |
| `YOLO_MODEL_NAME` | Weights file for detection | `best.pt` |
| `RISK_THRESHOLDS` | Limits for Green/Amber/Red status | 0.3/0.5/0.7 |

---
*Developed by the CrowdCare Team | 2026*