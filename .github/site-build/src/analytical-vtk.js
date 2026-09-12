import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import vtkGenericRenderWindow from '@kitware/vtk.js/Rendering/Misc/GenericRenderWindow';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkSphereMapper from '@kitware/vtk.js/Rendering/Core/SphereMapper';
import '@kitware/vtk.js/Rendering/OpenGL/SphereMapper';
import vtkCubeAxesActor from '@kitware/vtk.js/Rendering/Core/CubeAxesActor';
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
import vtkPolyDataNormals from '@kitware/vtk.js/Filters/Core/PolyDataNormals';

const DEFAULT_BG = [0.006, 0.018, 0.032];
const DEFAULT_POS = [0.235, 0.98, 0.824];
const DEFAULT_NEG = [0.898, 0.29, 0.353];
const DEFAULT_NEUTRAL = [0.239, 0.682, 0.827];
const DEFAULT_DARK = [0.035, 0.075, 0.105];
const finite = (value) => typeof value === 'number' && Number.isFinite(value);

function bounds(values) {
  let low = Infinity, high = -Infinity;
  for (const value of values) if (finite(value)) { low = Math.min(low, value); high = Math.max(high, value); }
  if (!Number.isFinite(low)) return [0, 1];
  if (low === high) return [low - .5, high + .5];
  return [low, high];
}

function normalizeColor(value, fallback) {
  if (!value) return fallback;
  if (Array.isArray(value) && value.length >= 3) return value.slice(0, 3).map((part) => Math.max(0, Math.min(1, Number(part))));
  if (typeof value === 'string') {
    const hex = value.replace('#', '');
    if (/^[0-9a-f]{6}$/i.test(hex)) return [0, 2, 4].map((offset) => parseInt(hex.slice(offset, offset + 2), 16) / 255);
  }
  return fallback;
}

function colorTransfer(range, palette) {
  const lut = vtkColorTransferFunction.newInstance();
  const [low, high] = range;
  const stops = Array.isArray(palette) && palette.length >= 2 ? palette : (
    low < 0 && high > 0
      ? [[0, DEFAULT_NEG], [Math.max(0, Math.min(1, -low / (high - low))), DEFAULT_DARK], [1, DEFAULT_POS]]
      : [[0, DEFAULT_DARK], [.45, DEFAULT_NEUTRAL], [1, DEFAULT_POS]]
  );
  for (const [position, rawColor] of stops) {
    const value = low + Math.max(0, Math.min(1, Number(position))) * (high - low);
    const color = normalizeColor(rawColor, DEFAULT_NEUTRAL);
    lut.addRGBPoint(value, color[0], color[1], color[2]);
  }
  lut.setMappingRange(low, high);
  return lut;
}

function configureScalarMapper(mapper, polyData, scalars, palette) {
  mapper.setInputData(polyData);
  if (scalars?.length) {
    const range = bounds(scalars);
    const array = vtkDataArray.newInstance({ name: 'tc-value', values: Float32Array.from(scalars), numberOfComponents: 1 });
    polyData.getPointData().setScalars(array);
    mapper.setScalarModeToUsePointData();
    mapper.setColorByArrayName('tc-value');
    mapper.setScalarRange(range[0], range[1]);
    mapper.setLookupTable(colorTransfer(range, palette));
    mapper.setUseLookupTableScalarRange(true);
  } else mapper.setScalarVisibility(false);
  return mapper;
}

function scalarMapper(polyData, scalars, palette) {
  return configureScalarMapper(vtkMapper.newInstance(), polyData, scalars, palette);
}

function pointReferenceSpan(groups) {
  const points = (Array.isArray(groups) ? groups : []).flatMap((group) => Array.isArray(group?.points) ? group.points : []);
  if (!points.length) return 1;
  const xs = points.map((point) => point?.[0]).filter(finite);
  const ys = points.map((point) => point?.[1]).filter(finite);
  const zs = points.map((point) => point?.[2]).filter(finite);
  const spans = [bounds(xs), bounds(ys), bounds(zs)].map(([low, high]) => high - low);
  return Math.max(...spans, 1e-3);
}

function surfaceActor(spec) {
  const x = spec.x || [], y = spec.y || [], z = spec.z || [];
  if (x.length < 2 || y.length < 2 || z.length !== y.length || z.some((row) => !Array.isArray(row) || row.length !== x.length)) throw new Error('Surface data must be a rectangular x/y/z grid');
  const points = [], values = [], cells = [];
  const scalarRows = spec.scalars || z;
  for (let row = 0; row < y.length; row += 1) for (let col = 0; col < x.length; col += 1) {
    const value = z[row][col];
    if (!finite(value)) throw new Error('Surface contains a non-finite z value');
    points.push(x[col], y[row], value);
    values.push(finite(scalarRows?.[row]?.[col]) ? scalarRows[row][col] : value);
  }
  for (let row = 0; row < y.length - 1; row += 1) for (let col = 0; col < x.length - 1; col += 1) {
    const a = row * x.length + col, b = a + 1, c = a + x.length, d = c + 1;
    cells.push(3, a, b, d, 3, a, d, c);
  }
  const poly = vtkPolyData.newInstance();
  poly.getPoints().setData(Float32Array.from(points), 3);
  poly.getPolys().setData(Uint32Array.from(cells));
  const normals = vtkPolyDataNormals.newInstance({computePointNormals: true, computeCellNormals: false});
  normals.setInputData(poly);
  normals.update();
  const shaded = normals.getOutputData();
  const actor = vtkActor.newInstance();
  actor.setMapper(scalarMapper(shaded, values, spec.palette));
  const property = actor.getProperty();
  property.setInterpolationToPhong();
  property.setAmbient(.18); property.setDiffuse(.72); property.setSpecular(.32); property.setSpecularPower(34);
  property.setEdgeVisibility(spec.edges === true);
  property.setEdgeColor(...normalizeColor(spec.edgeColor, [0.12, .48, .58]));
  return { actor, poly: shaded, bounds: shaded.getBounds() };
}

function pointsActor(spec, referenceSpan = 1) {
  const points = Array.isArray(spec.points) ? spec.points : [];
  if (!points.length || points.some((point) => !Array.isArray(point) || point.length < 3 || point.slice(0, 3).some((value) => !finite(value)))) throw new Error('Point cloud requires finite [x,y,z] points');
  const flat = points.flatMap((point) => point.slice(0, 3));
  const poly = vtkPolyData.newInstance();
  poly.getPoints().setData(Float32Array.from(flat), 3);
  const scalars = Array.isArray(spec.scalars) && spec.scalars.length === points.length ? spec.scalars : null;
  const pointBounds = poly.getBounds();
  const visualSize = finite(spec.pointSize) && spec.pointSize > 0 ? spec.pointSize : 7;
  const radius = finite(spec.radius) && spec.radius > 0 ? spec.radius : Math.max(referenceSpan * visualSize * .0028, referenceSpan * .0045);
  const mapper = configureScalarMapper(vtkSphereMapper.newInstance({ radius }), poly, scalars, spec.palette);
  const actor = vtkActor.newInstance();
  actor.setMapper(mapper);
  const property = actor.getProperty();
  if (!scalars) property.setColor(...normalizeColor(spec.color, DEFAULT_NEUTRAL));
  property.setAmbient(.22); property.setDiffuse(.72); property.setSpecular(.52); property.setSpecularPower(48);
  return { actor, poly, bounds: pointBounds };
}

function lineActor(spec) {
  const series = Array.isArray(spec.points) ? spec.points : [];
  if (series.length < 2 || series.some((point) => !Array.isArray(point) || point.length < 3 || point.slice(0, 3).some((value) => !finite(value)))) throw new Error('Line requires finite [x,y,z] points');
  const poly = vtkPolyData.newInstance();
  poly.getPoints().setData(Float32Array.from(series.flatMap((point) => point.slice(0, 3))), 3);
  poly.getLines().setData(Uint32Array.from([series.length, ...series.map((_, index) => index)]));
  const mapper = vtkMapper.newInstance(); mapper.setInputData(poly); mapper.setScalarVisibility(false);
  const actor = vtkActor.newInstance(); actor.setMapper(mapper);
  const property = actor.getProperty(); property.setColor(...normalizeColor(spec.color, DEFAULT_NEUTRAL)); property.setLineWidth(Math.max(1, Number(spec.width) || 2)); property.setAmbient(1); property.setDiffuse(0);
  return { actor, poly, bounds: poly.getBounds() };
}

function unionBounds(items) {
  const result = [Infinity, -Infinity, Infinity, -Infinity, Infinity, -Infinity];
  for (const item of items) for (let axis = 0; axis < 3; axis += 1) { result[axis * 2] = Math.min(result[axis * 2], item.bounds[axis * 2]); result[axis * 2 + 1] = Math.max(result[axis * 2 + 1], item.bounds[axis * 2 + 1]); }
  return result.every(Number.isFinite) ? result : [0, 1, 0, 1, 0, 1];
}

function scaledBounds(source, scale) {
  const out = [];
  for (let axis = 0; axis < 3; axis += 1) {
    const a = source[axis * 2] * scale[axis], b = source[axis * 2 + 1] * scale[axis];
    out.push(Math.min(a, b), Math.max(a, b));
  }
  return out;
}

function formatTick(value) {
  const magnitude = Math.abs(value);
  if (magnitude >= 1000 || (magnitude > 0 && magnitude < .001)) return value.toExponential(1);
  if (magnitude >= 100) return value.toFixed(0);
  if (magnitude >= 10) return value.toFixed(1).replace(/\.0$/, '');
  return value.toFixed(2).replace(/\.?0+$/, '');
}

function semanticTickGenerator(sourceBounds, scale, count = 4, showText = false) {
  return () => {
    const ticks = [[], [], []], tickStrings = [[], [], []];
    for (let axis = 0; axis < 3; axis += 1) {
      const low = sourceBounds[axis * 2], high = sourceBounds[axis * 2 + 1];
      for (let step = 0; step <= count; step += 1) {
        const value = low + (high - low) * step / count;
        ticks[axis].push(value * scale[axis]);
        tickStrings[axis].push(showText ? formatTick(value) : '');
      }
    }
    return { ticks, tickStrings };
  };
}

export function mountAnalytical3D(container, spec = {}) {
  if (!(container instanceof Element)) throw new TypeError('Analytical 3D container is required');
  container.replaceChildren(); container.dataset.renderer = 'vtk-webgl'; container.classList.add('tc-vtk3d');
  const renderWindow = vtkGenericRenderWindow.newInstance({ background: normalizeColor(spec.background, DEFAULT_BG), listenWindowResize: false });
  renderWindow.setContainer(container); renderWindow.resize();
  const renderer = renderWindow.getRenderer(), window = renderWindow.getRenderWindow(), actors = [];
  const pointSpan = pointReferenceSpan(spec.points);
  if (spec.surface) actors.push(surfaceActor(spec.surface));
  for (const points of spec.points || []) actors.push(pointsActor(points, pointSpan));
  for (const lines of spec.lines || []) actors.push(lineActor(lines));
  if (!actors.length) { renderWindow.delete(); throw new Error('Analytical 3D scene has no renderable layers'); }
  actors.forEach(({ actor }) => renderer.addActor(actor));
  const sceneBounds = unionBounds(actors);
  const spans = [sceneBounds[1] - sceneBounds[0], sceneBounds[3] - sceneBounds[2], sceneBounds[5] - sceneBounds[4]].map((span) => Math.max(Math.abs(span), 1e-9));
  const maxSpan = Math.max(...spans);
  const displayScale = spec.normalizeAxes === false ? [1, 1, 1] : spans.map((span) => Math.max(.2, Math.min(8, maxSpan / span)));
  actors.forEach(({ actor }) => actor.setScale(...displayScale));
  container.dataset.axisScale = JSON.stringify(displayScale);
  const camera = renderer.getActiveCamera();
  const displayBounds = scaledBounds(sceneBounds, displayScale);
  const axisLabels = spec.axisLabels || ['X', 'Y', 'Z'];
  const showAxisTextInScene = spec.axisTextInScene === true;
  const axes = vtkCubeAxesActor.newInstance({
    camera,
    dataBounds: displayBounds,
    generateTicks: semanticTickGenerator(sceneBounds, displayScale, 4, spec.axisTickLabels === true),
    gridLines: spec.gridLines !== false,
    boundsScaleFactor: 1.025,
    faceVisibilityAngle: finite(spec.axisFaceVisibilityAngle) ? spec.axisFaceVisibilityAngle : 32,
    axisTitlePixelOffset: 28,
    tickLabelPixelOffset: 8,
    axisTextStyle: { fontColor: '#8fd9ee', fontSize: 12, fontFamily: 'Inter, system-ui, sans-serif' },
    tickTextStyle: { fontColor: '#557c8f', fontSize: 9, fontFamily: 'Inter, system-ui, sans-serif' },
  });
  // vtkCubeAxesActor resets labels during construction, so semantic labels must
  // be set after newInstance rather than passed only as initial values.
  axes.setAxisLabels(...(showAxisTextInScene ? axisLabels : ['', '', '']));
  axes.getProperty().setColor(.10, .38, .48); renderer.addActor(axes);
  const axisKey = document.createElement('div');
  axisKey.className = 'tc-vtk3d-axis-key';
  axisKey.dataset.vtkAxisKey = 'true';
  axisKey.setAttribute('aria-hidden', 'true');
  axisKey.innerHTML = axisLabels.map((label, axis) => `<span><b>${['X','Y','Z'][axis]}</b><i>${String(label)}</i><em>${formatTick(sceneBounds[axis * 2])}&rarr;${formatTick(sceneBounds[axis * 2 + 1])}</em></span>`).join('');
  container.append(axisKey);
  const resetCamera = () => {
    const azimuth = (finite(spec.azimuth) ? spec.azimuth : 34) * Math.PI / 180;
    const elevation = (finite(spec.elevation) ? spec.elevation : 24) * Math.PI / 180;
    const cosElevation = Math.cos(elevation);
    camera.setViewUp(0, 0, 1);
    camera.setFocalPoint(0, 0, 0);
    camera.setPosition(cosElevation * Math.cos(azimuth), -cosElevation * Math.sin(azimuth), Math.sin(elevation));
    renderer.resetCamera(displayBounds);
    camera.zoom(finite(spec.cameraZoom) && spec.cameraZoom > 0 ? spec.cameraZoom : 1.12);
    renderer.resetCameraClippingRange(displayBounds);
    window.render();
  };
  resetCamera();
  const resizeObserver = new ResizeObserver(() => { renderWindow.resize(); window.render(); }); resizeObserver.observe(container);
  return {
    renderer: 'vtk-webgl',
    resetCamera,
    render: () => window.render(),
    resize: () => renderWindow.resize(),
    rotate(azimuth = 0, elevation = 0) {
      if (finite(azimuth)) camera.azimuth(azimuth);
      if (finite(elevation)) camera.elevation(elevation);
      renderer.resetCameraClippingRange();
      window.render();
    },
    zoom(factor = 1) {
      if (finite(factor) && factor > 0) camera.zoom(factor);
      renderer.resetCameraClippingRange();
      window.render();
    },
    dispose() { resizeObserver.disconnect(); renderWindow.setContainer(null); renderWindow.delete(); container.replaceChildren(); container.removeAttribute('data-renderer'); },
  };
}

export const ANALYTICAL_3D_ENGINE = Object.freeze({ name: 'vtk.js', version: '36.14.2', schema: 'tc.analytical-3d.v1' });
