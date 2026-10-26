# 🏔️ NER-SARTHI
> **North-Eastern Region - Smart Logistics & Accessibility Intelligence Platform**  
> *Making disaster-prone mountain logistics predictive, resilient, and life-saving.*

---

## 📌 Project Overview

In the mountainous corridors of North-East India (such as the NH-10 connecting Siliguri to Gangtok), extreme weather events like monsoons, cloudbursts, and seismic shifts trigger devastating, sudden landslides. 

Standard navigation tools (like Google Maps) are built for urban plains. They are **reactive**—routing emergency convoy vehicles directly onto blocked, high-risk passes, leading to stranded relief, supply chain lockouts, and lost "golden hours."

**NER-SARTHI** is an AI-powered, software-only, **terrain-aware logistics and routing platform** designed specifically to protect lives and maintain vital supply chains in geologically fragile environments.

---

## 🧠 Key Features

*   **⚡ Predictive Landslide Vulnerability (LVI):** Fuses dynamic meteorological data (live rainfall) with topological parameters (slope angle, historical frequency) to calculate a real-time hazard index for every 100m road corridor.
*   **🗺️ Terrain-Aware Routing Engine:** Utilizes a custom Dijkstra-based graph routing algorithm that applies a safety-risk penalty multiplier to edge weights. It proactively calculates mathematically safer, landslide-avoiding bypasses before blockages physically occur.
*   **📶 Offline-First Resiliency (Zero-Network Valleys):** Caches local vector tiles and pre-calculated routing graphs on-device using a Service Worker and local database. The application remains fully functional during critical deep-valley communication blackouts.
*   **💬 GenAI Tactical Dispatcher:** A conversational interface allowing emergency control room operators to issue natural-language routing commands (e.g., *"Dispatch oxygen tanks safely from Siliguri to Gangtok avoiding active rain zones"*). The system automatically translates the prompt, simulates constraints, and plots the safest route.

---

## 🛠️ Tech Stack

### Backend (Core Processing & Routing API)
*   **Python & FastAPI:** High-performance, async REST API endpoints.
*   **NetworkX:** Custom graph modeling, node clustering, and dynamic Dijkstra/A* routing.
*   **GeoPandas & Shapely:** Core geospatial data processing and spatial querying.

### Frontend & Offline-Edge
*   **Leaflet.js:** Lightweight interactive map layouts utilizing open-source OpenStreetMap (OSM) vector data.
*   **Tailwind CSS:** Fully responsive, modern, and high-visibility user dashboard UI.
*   **Service Workers & LocalStorage:** Client-side network interception, caching, and offline state persistence.

### AI & NLP Layer
*   **LVI Heuristic Predictor:** Mathematical risk model capturing exponential risk factors (Slope + Rain saturation).
*   **LangChain / Gemini API:** Natural language intent processing and structured payload conversion for dispatch automation.

---

## 📁 Repository Structure

```text
NER-SARTHI/
├── backend/
│   ├── data/
│   │   └── road_network.py        # Graph mapping of critical NE road networks
│   ├── hazard_engine.py          # LVI calculation and weather simulators
│   ├── router.py                 # Custom risk-weighted Dijkstra algorithm
│   ├── dispatch_ai.py            # Natural Language command interface
│   ├── main.py                   # FastAPI application router & endpoints
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── index.html                # Responsive Dashboard (Leaflet + Tailwind)
│   └── sw.js                     # Offline Service Worker script
└── README.md                     # Project Documentation
