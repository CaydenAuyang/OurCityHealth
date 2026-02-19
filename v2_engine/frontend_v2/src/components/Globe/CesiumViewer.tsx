/**
 * CesiumViewer — full-screen 3D globe using direct CesiumJS (no resium).
 *
 * Eight-effect architecture:
 *
 *   1. Mount          []                  — creates Viewer once, adds atmosphere + bloom.
 *   2. ScoresMap sync [scoresMap]         — keeps scoresMapRef current.
 *   3. Cities         [cities]            — creates PointPrimitiveCollection once.
 *   4. Color update   [scoresMap,         — updates point colours/sizes in-place.
 *                      selectedCityId]
 *   5. Click handler  [setSelectedCity]   — registers LEFT_CLICK.
 *   6. Fly-to         [selectedCityId,    — smooth camera fly-to.
 *                      cities]
 *   7. Hover tooltip  []                  — MOUSE_MOVE for HTML tooltip.
 *   8. Districts      [selectedCityId]    — fetch+render district polygons
 *                                           when zoomed < 200 km.
 */

import { useRef, useEffect, useMemo } from "react";
import {
  Ion,
  Viewer,
  Color,
  Cartesian3,
  Cartesian2,
  PointPrimitiveCollection,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  Math as CesiumMath,
  defined,
  GeoJsonDataSource,
} from "cesium";

import { useCities, useCityScores } from "../../api/hooks";
import { apiClient } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { scoreToHex, countryFlag, formatPopulation } from "../../lib/utils";
import type { City } from "../../api/types";

// ------------------------------------------------------------------ //
// Colour helpers                                                       //
// ------------------------------------------------------------------ //

function cssToColor(css: string, alpha = 1.0): Color {
  return Color.fromCssColorString(css).withAlpha(alpha);
}

const NO_DATA_COLOR = Color.fromCssColorString("rgba(255,255,255,0.35)");

function buildColor(
  cityId: string,
  scoresMap: Record<string, number>,
  selectedCityId: string | null,
): Color {
  if (cityId === selectedCityId) return cssToColor("#00d4ff", 1.0);
  const score = scoresMap[cityId] ?? null;
  if (score == null) return NO_DATA_COLOR;
  return cssToColor(scoreToHex(score), 0.95);
}

function buildSize(score: number | null, isSelected: boolean): number {
  if (isSelected) return 14;
  if (score == null) return 4;
  return Math.max(6, Math.min(14, 6 + Math.abs(score - 50) * 0.16));
}

// ------------------------------------------------------------------ //
// CesiumGlobe                                                          //
// ------------------------------------------------------------------ //

export function CesiumGlobe() {
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const viewerRef = useRef<Viewer | null>(null);
  const collectionRef = useRef<PointPrimitiveCollection | null>(null);

  // Districts ref
  const districtDsRef = useRef<GeoJsonDataSource | null>(null);
  const districtCityRef = useRef<string | null>(null);

  const scoresMapRef = useRef<Record<string, number>>({});
  const citiesRef = useRef<City[]>([]);

  const { selectedDate, selectedCityId, setSelectedCity } = useAppStore();
  const { data: cities = [] } = useCities();
  const { data: scores = [] } = useCityScores(selectedDate);

  const scoresMap = useMemo(() => {
    const map: Record<string, number> = {};
    scores.forEach((s) => { map[s.city_id] = s.stability_score; });
    return map;
  }, [scores]);

  useEffect(() => { citiesRef.current = cities; }, [cities]);

  // ---- Effect 1: create Viewer once on mount ---- //
  useEffect(() => {
    if (!containerRef.current) return;

    Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_TOKEN || "";

    const creditDiv = document.createElement("div");
    creditDiv.style.display = "none";

    viewerRef.current = new Viewer(containerRef.current, {
      timeline: false,
      animation: false,
      homeButton: false,
      baseLayerPicker: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      geocoder: false,
      infoBox: false,
      selectionIndicator: false,
      scene3DOnly: true,
      creditContainer: creditDiv,
    });

    const viewer = viewerRef.current;

    viewer.scene.globe.enableLighting = true;
    if (viewer.scene.skyAtmosphere) {
      viewer.scene.skyAtmosphere.show = true;
    }
    viewer.scene.fog.enabled = true;
    viewer.scene.fog.density = 0.0002;
    viewer.scene.globe.showGroundAtmosphere = true;

    try {
      viewer.scene.postProcessStages.bloom.enabled = true;
      viewer.scene.postProcessStages.bloom.uniforms.brightness = -0.2;
      viewer.scene.postProcessStages.bloom.uniforms.delta = 0.7;
      viewer.scene.postProcessStages.bloom.uniforms.sigma = 3.0;
      viewer.scene.postProcessStages.bloom.uniforms.stepSize = 0.5;
    } catch (_) {}

    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
      }
      viewerRef.current = null;
      collectionRef.current = null;
    };
  }, []);

  // ---- Effect 2: keep scoresMapRef current ---- //
  useEffect(() => { scoresMapRef.current = scoresMap; }, [scoresMap]);

  // ---- Effect 3: create PointPrimitiveCollection when cities load ---- //
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed() || cities.length === 0) return;

    const currentScores = scoresMapRef.current;
    const collection = new PointPrimitiveCollection();

    cities.forEach((city: City) => {
      const score = currentScores[city.id] ?? null;
      collection.add({
        position: Cartesian3.fromDegrees(city.longitude, city.latitude),
        color: buildColor(city.id, currentScores, null),
        pixelSize: buildSize(score, false),
        outlineColor: score != null ? Color.BLACK : Color.TRANSPARENT,
        outlineWidth: score != null ? 1 : 0,
        id: { cityId: city.id, cityName: city.name },
      });
    });

    viewer.scene.primitives.add(collection);
    collectionRef.current = collection;

    return () => {
      const v = viewerRef.current;
      if (v && !v.isDestroyed()) {
        v.scene.primitives.remove(collection);
        collection.destroy();
      }
      collectionRef.current = null;
    };
  }, [cities]);

  // ---- Effect 4: update colours in-place on score / selection change ---- //
  useEffect(() => {
    const collection = collectionRef.current;
    if (!collection || collection.isDestroyed()) return;

    for (let i = 0; i < collection.length; i++) {
      const point = collection.get(i);
      const cityId = point.id?.cityId as string | undefined;
      if (!cityId) continue;

      const isSelected = cityId === selectedCityId;
      const score = scoresMap[cityId] ?? null;
      point.color = buildColor(cityId, scoresMap, selectedCityId);
      point.pixelSize = buildSize(score, isSelected);
      if (isSelected) {
        point.outlineColor = cssToColor("#00d4ff", 0.9);
        point.outlineWidth = 2;
      } else if (score != null) {
        point.outlineColor = Color.BLACK;
        point.outlineWidth = 1;
      } else {
        point.outlineColor = Color.TRANSPARENT;
        point.outlineWidth = 0;
      }
    }
  }, [scoresMap, selectedCityId]);

  // ---- Effect 5: click handler ---- //
  useEffect(() => {
    const frameId = requestAnimationFrame(() => {
      const viewer = viewerRef.current;
      if (!viewer || viewer.isDestroyed()) return;

      const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);

      handler.setInputAction((event: { position: Cartesian2 }) => {
        const picked = viewer.scene.pick(event.position);
        if (
          defined(picked) &&
          picked.id &&
          typeof picked.id.cityId === "string"
        ) {
          setSelectedCity(picked.id.cityId, picked.id.cityName);
        } else {
          setSelectedCity(null);
        }
      }, ScreenSpaceEventType.LEFT_CLICK);

      (viewer as Viewer & { _hudClickHandler?: ScreenSpaceEventHandler })
        ._hudClickHandler = handler;
    });

    return () => {
      cancelAnimationFrame(frameId);
      const viewer = viewerRef.current;
      const handler = (
        viewer as (Viewer & { _hudClickHandler?: ScreenSpaceEventHandler }) | null
      )?._hudClickHandler;
      if (handler && !handler.isDestroyed()) handler.destroy();
    };
  }, [setSelectedCity]);

  // ---- Effect 6: fly-to on city selection ---- //
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed() || !selectedCityId) return;

    const city = cities.find((c) => c.id === selectedCityId);
    if (!city) return;

    viewer.trackedEntity = undefined;

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(city.longitude, city.latitude, 1_500_000),
      duration: 1.5,
      orientation: {
        heading: 0,
        pitch: CesiumMath.toRadians(-90),
        roll: 0,
      },
    });
  }, [selectedCityId, cities]);

  // ---- Effect 7: hover tooltip ---- //
  useEffect(() => {
    const frameId = requestAnimationFrame(() => {
      const viewer = viewerRef.current;
      const tooltip = tooltipRef.current;
      if (!viewer || viewer.isDestroyed() || !tooltip) return;

      const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);

      handler.setInputAction((movement: { endPosition: Cartesian2 }) => {
        const picked = viewer.scene.pick(movement.endPosition);
        if (
          defined(picked) &&
          picked.id &&
          typeof picked.id.cityId === "string"
        ) {
          const cityId = picked.id.cityId as string;
          const city = citiesRef.current.find((c) => c.id === cityId);
          if (!city) {
            tooltip.style.display = "none";
            return;
          }

          const score = scoresMapRef.current[cityId] ?? null;
          const flag = countryFlag(city.country_code);
          const pop = formatPopulation(city.population);

          let scoreHtml: string;
          if (score != null) {
            const color = scoreToHex(score);
            scoreHtml = `Stability: ${score.toFixed(1)} <span style="color:${color};">&#11044;</span>`;
          } else {
            scoreHtml = `<span style="color:#64748b;">No GDELT data</span>`;
          }

          tooltip.innerHTML = `
            <div style="font-weight:600;margin-bottom:2px;">${flag} ${city.name}</div>
            <div style="color:#94a3b8;font-size:10px;">Pop: ${pop}</div>
            <div style="font-size:10px;">${scoreHtml}</div>
          `;

          const canvasRect = viewer.scene.canvas.getBoundingClientRect();
          const x = movement.endPosition.x + canvasRect.left + 15;
          const y = movement.endPosition.y + canvasRect.top + 15;
          tooltip.style.left = `${x}px`;
          tooltip.style.top = `${y}px`;
          tooltip.style.display = "block";
        } else {
          tooltip.style.display = "none";
        }
      }, ScreenSpaceEventType.MOUSE_MOVE);

      (viewer as Viewer & { _hudHoverHandler?: ScreenSpaceEventHandler })
        ._hudHoverHandler = handler;
    });

    return () => {
      cancelAnimationFrame(frameId);
      const viewer = viewerRef.current;
      const handler = (
        viewer as (Viewer & { _hudHoverHandler?: ScreenSpaceEventHandler }) | null
      )?._hudHoverHandler;
      if (handler && !handler.isDestroyed()) handler.destroy();
    };
  }, []);

  // ---- Effect 8: district polygons when zoomed in on selected city ---- //
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;

    let cancelled = false;

    const removeDistricts = () => {
      if (districtDsRef.current) {
        try { viewer.dataSources.remove(districtDsRef.current, true); } catch (_) {}
        districtDsRef.current = null;
        districtCityRef.current = null;
      }
    };

    const maybeLoadDistricts = async () => {
      const height = viewer.camera.positionCartographic.height;
      const cityId = useAppStore.getState().selectedCityId;

      if (!cityId || height > 200_000) {
        removeDistricts();
        return;
      }

      if (districtCityRef.current === cityId) return;

      removeDistricts();

      try {
        const geojson = await apiClient.getDistricts(cityId);
        if (cancelled || geojson.features.length === 0) return;

        const ds = await GeoJsonDataSource.load(geojson, {
          fill: Color.fromCssColorString("rgba(0,212,255,0.15)"),
          stroke: Color.fromCssColorString("rgba(0,212,255,0.5)"),
          strokeWidth: 1,
          clampToGround: true,
        });

        if (cancelled) return;

        viewer.dataSources.add(ds);
        districtDsRef.current = ds;
        districtCityRef.current = cityId;
      } catch (_) {
        // No districts available or network error — silent
      }
    };

    maybeLoadDistricts();

    const removeCamListener = viewer.camera.changed.addEventListener(() => {
      maybeLoadDistricts();
    });

    return () => {
      cancelled = true;
      removeCamListener();
      removeDistricts();
    };
  }, [selectedCityId]);

  return (
    <>
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />

      {/* Hover tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 pointer-events-none"
        style={{ display: "none" }}
      >
        <div
          className="px-3 py-2 rounded-lg font-mono text-xs text-slate-100"
          style={{
            background: "rgba(5, 10, 25, 0.88)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            border: "1px solid rgba(0, 200, 255, 0.25)",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.6), 0 0 12px rgba(0, 150, 255, 0.08)",
          }}
        />
      </div>
    </>
  );
}

// ------------------------------------------------------------------ //
// Score legend                                                         //
// ------------------------------------------------------------------ //

export function ScoreLegend() {
  const ITEMS = [
    { label: "Excellent (\u226580)", color: "rgb(16,185,129)" },
    { label: "Good (65\u201379)", color: "rgb(34,197,94)" },
    { label: "Mixed (40\u201364)", color: "rgb(234,179,8)" },
    { label: "Poor (20\u201339)", color: "rgb(249,115,22)" },
    { label: "Crisis (<20)", color: "rgb(220,38,38)" },
    { label: "No data", color: "rgba(255,255,255,0.15)" },
  ] as const;

  return (
    <div className="flex flex-col gap-1.5">
      {ITEMS.map(({ label, color }) => (
        <div key={label} className="flex items-center gap-2">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ background: color }}
          />
          <span className="text-xs text-slate-400 font-mono">{label}</span>
        </div>
      ))}
    </div>
  );
}
