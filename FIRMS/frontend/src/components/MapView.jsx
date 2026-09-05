import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import "./MapView.css";
import "maplibre-gl/dist/maplibre-gl.css";

function MapView({
  observations = [],
  onObservationSelect,
  selectedObservation,
  center,
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);

  // --------------------------------------------------------
  // Initialize map ONCE
  // --------------------------------------------------------

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const newMap = new maplibregl.Map({
      container: mapContainer.current,

      style: {
        version: 8,

        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },

        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },

      center: center || [69.85, 22.35],
      zoom: 9,
    });

    newMap.addControl(
      new maplibregl.NavigationControl(),
      "top-right"
    );

    map.current = newMap;

    return () => {
      newMap.remove();
      map.current = null;
    };
  }, []);

  // --------------------------------------------------------
  // Update map center when region changes
  // --------------------------------------------------------
  useEffect(() => {
    if (!map.current || !center) return;
    map.current.flyTo({ center: center, zoom: 9, essential: true, duration: 1500 });
  }, [center]);

  // --------------------------------------------------------
  // Fly to selected observation
  // --------------------------------------------------------

  useEffect(() => {
    if (!map.current || !selectedObservation) return;
    const lat = Number(selectedObservation.latitude);
    const lon = Number(selectedObservation.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      map.current.flyTo({
        center: [lon, lat],
        zoom: 13,
        essential: true,
      });
    }
  }, [selectedObservation]);

  // --------------------------------------------------------
  // Draw observations whenever API data changes
  // --------------------------------------------------------

  useEffect(() => {
    const currentMap = map.current;

    if (!currentMap) return;

    const draw = () => {
      if (!currentMap.isStyleLoaded()) return;

      console.log(
        "Drawing thermal observations:",
        observations.length
      );

      // ----------------------------------------------
      // Remove existing layer/source
      // ----------------------------------------------

      if (currentMap.getLayer("thermal-points")) {
        currentMap.removeLayer("thermal-points");
      }

      if (currentMap.getSource("thermal-observations")) {
        currentMap.removeSource("thermal-observations");
      }

      // ----------------------------------------------
      // Validate coordinates
      // ----------------------------------------------

      const validObservations = observations.filter((item) => {
        const lat = Number(item.latitude);
        const lon = Number(item.longitude);

        return (
          Number.isFinite(lat) &&
          Number.isFinite(lon) &&
          lat >= -90 &&
          lat <= 90 &&
          lon >= -180 &&
          lon <= 180
        );
      });

      console.log(
        "Valid observations:",
        validObservations.length
      );

      if (validObservations.length === 0) {
        return;
      }

      // ----------------------------------------------
      // Create GeoJSON
      // ----------------------------------------------

      const features = validObservations.map(
        (item, index) => {
          const lat = Number(item.latitude);
          const lon = Number(item.longitude);

          const frpValue = Number(item.frp);

          const behaviorScore =
            item.behavior_score !== null &&
            item.behavior_score !== undefined &&
            Number.isFinite(Number(item.behavior_score))
              ? Number(item.behavior_score)
              : null;

          return {
            type: "Feature",

            geometry: {
              type: "Point",
              coordinates: [lon, lat],
            },

            properties: {
              id: index,

              latitude: lat,
              longitude: lon,

              acq_date:
                item.acq_date ?? "—",

              acq_time:
                item.acq_time ?? "—",

              satellite:
                item.satellite ?? "—",

              confidence:
                item.confidence ?? "—",

              daynight:
                item.daynight ?? "—",

              frp:
                Number.isFinite(frpValue)
                  ? frpValue
                  : null,

              source_class:
                item.source_class_v2 ??
                item.source_class ??
                "UNKNOWN",

              classification_confidence:
                item.classification_confidence_v2 ??
                item.classification_confidence ??
                "—",

              evidence_strength:
                item.evidence_strength ??
                "—",

              evidence_summary:
                item.evidence_summary ??
                "—",

              classification_reason:
                item.classification_reason ??
                "—",

              interpretation:
                item.interpretation ??
                "—",

              worldcover_context:
                item.worldcover_context ??
                "—",

              association_type:
                item.association_type ??
                "—",

              association_confidence:
                item.association_confidence ??
                "—",

              facility_name:
                item.name ??
                item.facility_name ??
                "Unknown source",

              industrial:
                item.industrial ??
                "—",

              landuse:
                item.landuse ??
                "—",

              power:
                item.power ??
                "—",

              behavior_state:
                item.behavior_state ??
                "—",

              behavior_score:
                behaviorScore,

              persistence_state:
                item.persistence_state ??
                "—",

              investigation_priority:
                item.investigation_priority ??
                "LOW",

              observation_count:
                item.observation_count ??
                null,

              max_frp_mw:
                item.max_frp_mw ??
                null,

              total_frp_mw:
                item.total_frp_mw ??
                null,

              baseline_mean_frp:
                item.baseline_mean_frp ??
                null,

              baseline_p90_frp:
                item.baseline_p90_frp ??
                null,

              baseline_median_frp:
                item.baseline_median_frp ??
                null,

              baseline_std_frp:
                item.baseline_std_frp ??
                null,

              previous_active_days:
                item.previous_active_days ??
                null,

              frp_score:
                item.frp_score ??
                null,

              detection_score:
                item.detection_score ??
                null,

              frequency_score:
                item.frequency_score ??
                null,

              region_id:
                item.region_id ??
                null,
            },
          };
        }
      );

      // ----------------------------------------------
      // Add source
      // ----------------------------------------------

      currentMap.addSource(
        "thermal-observations",
        {
          type: "geojson",

          data: {
            type: "FeatureCollection",
            features,
          },
        }
      );

      // ----------------------------------------------
      // Add thermal points
      // ----------------------------------------------

      currentMap.addLayer({
        id: "thermal-points",

        type: "circle",

        source: "thermal-observations",

        paint: {
          // --------------------------------------------
          // Size
          // --------------------------------------------

          "circle-radius": [
            "case",

            [
              "==",
              ["get", "investigation_priority"],
              "HIGH",
            ],
            11,

            [
              "==",
              ["get", "investigation_priority"],
              "MEDIUM",
            ],
            8,

            [
              "interpolate",
              ["linear"],
              ["coalesce", ["get", "frp"], 0],

              0,
              4,

              5,
              6,

              10,
              8,

              20,
              10,

              30,
              13,
            ],
          ],

          // --------------------------------------------
          // Color
          // --------------------------------------------

          "circle-color": [
            "case",

            // HIGH
            [
              "==",
              ["get", "investigation_priority"],
              "HIGH",
            ],
            "#ff1744",

            // MEDIUM
            [
              "==",
              ["get", "investigation_priority"],
              "MEDIUM",
            ],
            "#ff9800",

            // Industrial
            [
              "==",
              ["get", "source_class"],
              "INDUSTRIAL_ASSOCIATED",
            ],
            "#ef4444",

            // Agricultural
            [
              "==",
              ["get", "source_class"],
              "AGRICULTURAL",
            ],
            "#f59e0b",

            // Forest
            [
              "==",
              ["get", "source_class"],
              "FOREST_NATURAL",
            ],
            "#22c55e",

            // Other
            [
              "==",
              ["get", "source_class"],
              "OTHER",
            ],
            "#a855f7",

            // Unknown
            "#38bdf8",
          ],

          "circle-opacity": 0.85,

          "circle-stroke-color": "#ffffff",

          "circle-stroke-width": [
            "case",

            [
              "==",
              ["get", "investigation_priority"],
              "HIGH",
            ],
            2,

            [
              "==",
              ["get", "investigation_priority"],
              "MEDIUM",
            ],
            1.5,

            1,
          ],
        },
      });


      // ----------------------------------------------
      // Click
      // ----------------------------------------------

      const handleClick = (event) => {
        const feature =
          event.features?.[0];

        if (!feature) return;

        const p = feature.properties;

        console.log(
          "Selected thermal observation:",
          p
        );

        if (onObservationSelect) {
          onObservationSelect({
            ...p,

            latitude: Number(p.latitude),

            longitude: Number(p.longitude),

            frp:
              p.frp !== null &&
              p.frp !== undefined &&
              p.frp !== ""
                ? Number(p.frp)
                : null,

            behavior_score:
              p.behavior_score !== null &&
              p.behavior_score !== undefined &&
              p.behavior_score !== ""
                ? Number(p.behavior_score)
                : null,
          });
        }
      };

      const handleEnter = () => {
        currentMap.getCanvas().style.cursor =
          "pointer";
      };

      const handleLeave = () => {
        currentMap.getCanvas().style.cursor =
          "";
      };

      currentMap.on(
        "click",
        "thermal-points",
        handleClick
      );

      currentMap.on(
        "mouseenter",
        "thermal-points",
        handleEnter
      );

      currentMap.on(
        "mouseleave",
        "thermal-points",
        handleLeave
      );

      // ----------------------------------------------
      // Cleanup event listeners
      // ----------------------------------------------

      return () => {
        currentMap.off(
          "click",
          "thermal-points",
          handleClick
        );

        currentMap.off(
          "mouseenter",
          "thermal-points",
          handleEnter
        );

        currentMap.off(
          "mouseleave",
          "thermal-points",
          handleLeave
        );
      };
    };

    // ----------------------------------------------
    // Wait for map style
    // ----------------------------------------------

    if (currentMap.isStyleLoaded()) {
      return draw();
    }

    const handleLoad = () => {
      draw();
    };

    currentMap.once(
      "load",
      handleLoad
    );

    return () => {
      currentMap.off(
        "load",
        handleLoad
      );

      if (
        currentMap.getLayer("thermal-points")
      ) {
        currentMap.removeLayer(
          "thermal-points"
        );
      }

      if (
        currentMap.getSource(
          "thermal-observations"
        )
      ) {
        currentMap.removeSource(
          "thermal-observations"
        );
      }
    };
  }, [observations, onObservationSelect]);

  return (
  <div className="map-container">
    <div
      ref={mapContainer}
      className="maplibre-map"
    />

    <div className="map-legend">
      <div className="map-legend-title">
        THERMAL INTELLIGENCE
      </div>

      <div className="legend-item">
        <span className="legend-dot legend-high" />
        <span>HIGH — investigate</span>
      </div>

      <div className="legend-item">
        <span className="legend-dot legend-medium" />
        <span>MEDIUM — review</span>
      </div>

      <div className="legend-item">
        <span className="legend-dot legend-industrial" />
        <span>Industrial-associated</span>
      </div>

      <div className="legend-item">
        <span className="legend-dot legend-agricultural" />
        <span>Agricultural</span>
      </div>

      <div className="legend-item">
        <span className="legend-dot legend-natural" />
        <span>Forest / natural</span>
      </div>

      <div className="legend-note">
        Marker size reflects thermal intensity.
      </div>
    </div>
  </div>
);
}

export default MapView;