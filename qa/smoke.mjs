import { chromium } from 'playwright';

const browser = await chromium.launch({headless:true});
const page = await browser.newPage({acceptDownloads:true, viewport:{width:1440,height:1000}});
const errors=[];
page.on('pageerror',e=>errors.push('pageerror: '+e.message));
page.on('console',msg=>{ if(msg.type()==='error') errors.push('console: '+msg.text()); });

await page.goto('http://127.0.0.1:8000/index.html',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelectorAll('#map-indicator option').length >= 10,{timeout:20000});
await page.waitForTimeout(2500);

const status=(await page.locator('#last-updated').innerText()).trim();
if(/data load error/i.test(status)) throw new Error('Application reports Data load error');

// Dynamic analytical layer + legend.
await page.selectOption('#map-indicator','dw_vulnerability');
await page.waitForTimeout(250);
if(!/Drinking Water vulnerability/i.test(await page.locator('#map-badge').innerText())) throw new Error('Map badge did not update for analytical layer');
if(!/Drinking Water vulnerability/i.test(await page.locator('#map-legend').innerText())) throw new Error('Legend did not update for analytical layer');

// District filtering uses the profile district name but spatial filtering uses PCODE internally.
await page.selectOption('#district-filter',{label:'Chitwan'});
await page.waitForTimeout(150);
const munOptions=await page.locator('#municipality-filter option').allTextContents();
if(!munOptions.some(x=>/Ichchhakamana/i.test(x))) throw new Error('Chitwan filter did not expose Ichchhakamana');

// Municipality profile renders and indicators do not duplicate class names.
await page.selectOption('#district-filter',{label:'Nuwakot'});
await page.selectOption('#municipality-filter','NP0328301');
await page.waitForTimeout(300);
if(!/Bidur/i.test(await page.locator('#profile-panel').innerText())) throw new Error('Bidur profile did not render');
await page.getByRole('button',{name:'Indicators'}).click();
const indicatorText=await page.locator('#profile-panel').innerText();
if(/Unknown\s+Unknown/i.test(indicatorText)) throw new Error('Duplicated Unknown label remains in indicator panel');
if(/Very High\s+Very High/i.test(indicatorText)) throw new Error('Duplicated severity label remains in indicator panel');

// Analysis filters and sorting.
await page.locator('.tab[data-view="analysis"]').click();
await page.locator('#analysis-search').fill('Bidur');
await page.waitForTimeout(100);
const rows=await page.locator('#analysis-table tbody tr').count();
if(rows!==1) throw new Error('Analysis search filter did not return exactly one Bidur row');
await page.locator('#analysis-search').fill('');
await page.locator('#analysis-table th[data-sort="municipality"]').click();

// About methodology.
await page.locator('.tab[data-view="about"]').click();
const about=await page.locator('#about-view').textContent();
for(const phrase of ['50%','30%','20%','Current WASH conditions','Data sources']){
  if(!about.includes(phrase)) throw new Error('About section missing: '+phrase);
}


// v16 final severity legend.
await page.locator('.tab[data-view="map"]').click();
await page.selectOption('#map-indicator','need');
await page.waitForTimeout(200);
const needLegend=await page.locator('#map-legend').innerText();
for(const [label,pattern] of [
  ['Very High >3.50',/Very High\s*>\s*3\.50/],
  ['High 3.00–3.50',/High\s*3\.00–3\.50/],
  ['Moderate 2.25–<3.00',/Moderate\s*2\.25–<3\.00/],
  ['Low 1.75–<2.25',/Low\s*1\.75–<2\.25/],
  ['Minimal <1.75',/Minimal\s*<\s*1\.75/]
]){
  if(!pattern.test(needLegend)) throw new Error('Need Score legend missing: '+label+'; got: '+needLegend);
}

// Overview must expose the new health and education context layers.
await page.locator('.tab[data-view="map"]').click();
const layers=await page.locator('#layer-list').innerText();
if(!/Health facilities/i.test(layers)||!/Education facilities/i.test(layers)) throw new Error('Overview facility layers are missing');
if(await page.locator('input[data-layer="holding"]').isChecked()) throw new Error('Holding centres should not be visible by default');
await page.locator('input[data-layer="health"]').check();
await page.locator('input[data-layer="education"]').check();
await page.waitForFunction(() => map.queryRenderedFeatures({layers:['education-circle']}).length>0,{timeout:8000});
await page.waitForFunction(() => map.queryRenderedFeatures({layers:['education-label']}).length>0,{timeout:8000});
const facilityRender=await page.evaluate(() => ({
  educationPoints: map.queryRenderedFeatures({layers:['education-circle']}).length,
  educationLabels: map.queryRenderedFeatures({layers:['education-label']}).length,
  healthPoints: map.queryRenderedFeatures({layers:['health-circle']}).length
}));
if(facilityRender.educationPoints<1) throw new Error('Education facility points did not render');
if(facilityRender.educationLabels<1) throw new Error('Education facility Latin-name labels did not render');
const schoolClick=await page.evaluate(() => {
  const f=map.queryRenderedFeatures({layers:['education-circle']})[0];
  if(!f) return null;
  const pt=map.project(f.geometry.coordinates);
  const rect=map.getContainer().getBoundingClientRect();
  return {x:rect.left+pt.x,y:rect.top+pt.y,label:f.properties.name_latin||f.properties.label||f.properties.name};
});
if(!schoolClick) throw new Error('Could not locate an education facility for click test');
await page.mouse.click(schoolClick.x,schoolClick.y);
await page.waitForTimeout(150);
const popupTexts=await page.locator('.maplibregl-popup-content').allTextContents();
if(!popupTexts.some(x=>x.includes(schoolClick.label))) throw new Error('Education facility click did not open facility popup using Latin label; popups='+popupTexts.join(' | '));

// Water Systems publication dashboard.
await page.goto('http://127.0.0.1:8000/infrastructure.html',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => /90 assessed water-supply schemes/i.test(document.querySelector('#status')?.textContent||''),{timeout:10000});
const infraText=await page.locator('body').innerText();
for(const [label,pattern] of [
  ['Water-supply schemes',/water-supply schemes/i],
  ['Beneficiary population',/beneficiary population/i],
  ['Reconstruction cost',/reconstruction cost/i],
  ['Condition profile',/condition profile/i],
  ['Where the burden is concentrated',/where the burden is concentrated/i],
  ['Classification key',/classification key/i]
]){
  if(!pattern.test(infraText)) throw new Error('Water Systems dashboard missing: '+label);
}
const bodyHtml=await page.locator('body').innerHTML();
if(/docs\.google\.com\/spreadsheets|gviz\/tq|LIVE_SHEET_ID|LIVE_CSV_URL|PDNA_CORRECTIONS_SHEET_ID/.test(bodyHtml)) throw new Error('Water Systems exposes direct Google Sheet access');
for(const href of ['index.html#overview','index.html#severity','index.html#methodology']){
  if(!bodyHtml.includes('href="'+href+'"')) throw new Error('Water Systems navigation missing '+href);
}
if(await page.locator('#kpis .kpi').count()!==4) throw new Error('Water Systems should render exactly four KPI cards');
await page.waitForFunction(() => window.map && map.isStyleLoaded && map.isStyleLoaded(),{timeout:10000});
await page.waitForTimeout(700);
const rendered=await page.evaluate(() => ({
  points: map.queryRenderedFeatures({layers:['pdna-points']}).length,
  polygons: map.queryRenderedFeatures({layers:['municipal-fill']}).length
}));
if(rendered.points<1) throw new Error('Water Systems map rendered no WSS points');
if(rendered.polygons<1) throw new Error('Water Systems map rendered no municipality polygons');
if(await page.locator('#municipality-indicator option').count()!==3) throw new Error('Municipality indicator selector should contain exactly three options');
if(await page.locator('#point-size option').count()!==2) throw new Error('Point size selector should contain exactly two options');
if(await page.locator('#damage-filter option').count()!==7) throw new Error('Global D0–D5 damage filter is incomplete');
if(await page.locator('#breakdown-damage option').count()!==7) throw new Error('Breakdown D0–D5 focus is incomplete');
await page.selectOption('#damage-filter','D5');
await page.waitForTimeout(100);
const d5Kpi=await page.locator('#kpis .kpi').first().innerText();
if(!/13/.test(d5Kpi)) throw new Error('Global D5 filter did not reduce scheme KPI to 13');
await page.selectOption('#damage-filter','');
const toggle=page.locator('#municipality-indicator-toggle');
await toggle.uncheck();
await page.waitForTimeout(100);
const fillVisibilityOff=await page.evaluate(() => map.getLayoutProperty('municipal-fill','visibility'));
if(fillVisibilityOff!=='none') throw new Error('Municipality shading toggle did not turn fill off');
await toggle.check();
await page.waitForTimeout(100);
const fillVisibilityOn=await page.evaluate(() => map.getLayoutProperty('municipal-fill','visibility'));
if(fillVisibilityOn!=='visible') throw new Error('Municipality shading toggle did not turn fill on');
const pointLegend=page.locator('#map-legend [data-point-legend="D5"]');
await pointLegend.click();
await page.waitForTimeout(100);
const legendFocused=await page.evaluate(() => map.getSource('pdna')._data.features.every(f=>f.properties.damage_grade==='D5'));
if(!legendFocused) throw new Error('Clickable point legend did not filter map to D5');
await pointLegend.click();
await page.selectOption('#breakdown-damage','D4');
await page.waitForTimeout(100);
if(!/D4/.test(await page.locator('#breakdown-note').innerText())) throw new Error('Geographic breakdown damage focus did not apply');
await page.selectOption('#breakdown-damage','');
if(!/D0/.test(await page.locator('#classification-key').innerText())||!/D5/.test(await page.locator('#classification-key').innerText())) throw new Error('D0–D5 definitions are missing');
await page.selectOption('#condition-variable','site_safety_grade');
await page.waitForTimeout(100);
const classKey=await page.locator('#classification-key').innerText();
if(!/S1/.test(classKey)||!/S5/.test(classKey)) throw new Error('S1–S5 definitions are missing');
await page.selectOption('#condition-variable','damage_grade');
const firstSegment=page.locator('#condition-chart .segment-btn').first();
await firstSegment.click();
await page.waitForTimeout(100);
if(!/Showing/.test(await page.locator('#breakdown-note').innerText())) throw new Error('Geographic breakdown did not respond to condition selection');
await page.selectOption('#breakdown-level','district');
await page.selectOption('#breakdown-measure','reconstruction_cost');
await page.selectOption('#point-size','reconstruction_cost_npr');
await page.selectOption('#municipality-indicator','reconstruction_cost');
await page.locator('#reset-map').click();
if((await page.locator('#municipality-indicator').inputValue())!=='need_score') throw new Error('Reset map did not restore municipality indicator');
if((await page.locator('#point-size').inputValue())!=='beneficiary_population') throw new Error('Reset map did not restore point-size variable');

// Deep-link routing on main application.
await page.goto('http://127.0.0.1:8000/index.html#severity',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelector('#analysis-view')?.classList.contains('active'),{timeout:10000});
await page.goto('http://127.0.0.1:8000/index.html#methodology',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelector('#about-view')?.classList.contains('active'),{timeout:10000});

// Return to Overview and verify export produces a download.
await page.goto('http://127.0.0.1:8000/index.html#overview',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelectorAll('#map-indicator option').length >= 10,{timeout:20000});
await page.locator('#export-map').click();
const [download] = await Promise.all([
  page.waitForEvent('download',{timeout:15000}),
  page.locator('#export-menu button[data-export="screen"]').click()
]);
const name=download.suggestedFilename();
if(!name.endsWith('.png')) throw new Error('Map export is not PNG');

if(errors.length) throw new Error('Browser errors: '+errors.join(' | '));
console.log('PASS browser smoke test:',status,'export=',name);
await browser.close();
