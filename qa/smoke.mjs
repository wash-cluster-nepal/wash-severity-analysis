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
await page.getByRole('button',{name:'Analysis'}).click();
await page.locator('#analysis-search').fill('Bidur');
await page.waitForTimeout(100);
const rows=await page.locator('#analysis-table tbody tr').count();
if(rows!==1) throw new Error('Analysis search filter did not return exactly one Bidur row');
await page.locator('#analysis-search').fill('');
await page.locator('#analysis-table th[data-sort="municipality"]').click();

// About methodology.
await page.getByRole('button',{name:'About'}).click();
const about=await page.locator('#about-view').textContent();
for(const phrase of ['50%','30%','20%','Current WASH conditions','Data sources']){
  if(!about.includes(phrase)) throw new Error('About section missing: '+phrase);
}


// Locked v15 final severity legend.
await page.getByRole('button',{name:'Map'}).click();
await page.selectOption('#map-indicator','need');
await page.waitForTimeout(200);
const needLegend=await page.locator('#map-legend').innerText();
for(const phrase of ['Very High  > 3.50','High  3.00–3.50','Moderate  2.25–<3.00','Low  1.75–<2.25','Minimal  < 1.75']){
  if(!needLegend.includes(phrase)) throw new Error('Need Score legend missing: '+phrase);
}

// Water Systems must not retrieve the private point Sheet and navigation must deep-link.
await page.goto('http://127.0.0.1:8000/infrastructure.html',{waitUntil:'domcontentloaded'});
await page.waitForTimeout(300);
const infraText=await page.locator('body').innerText();
if(/PDNA \/ DDA|Connecting to Cluster Google Sheet/i.test(infraText)) throw new Error('Water Systems contains stale/public live-source terminology');
const bodyHtml=await page.locator('body').innerHTML();
if(/docs\.google\.com\/spreadsheets|gviz\/tq|LIVE_SHEET_ID|LIVE_CSV_URL/.test(bodyHtml)) throw new Error('Water Systems exposes direct private Sheet access');
for(const href of ['index.html#map','index.html#analysis','index.html#about']){
  if(!bodyHtml.includes('href="'+href+'"')) throw new Error('Water Systems navigation missing '+href);
}

// Deep-link routing on main application.
await page.goto('http://127.0.0.1:8000/index.html#analysis',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelector('#analysis-view')?.classList.contains('active'),{timeout:10000});
await page.goto('http://127.0.0.1:8000/index.html#about',{waitUntil:'domcontentloaded'});
await page.waitForFunction(() => document.querySelector('#about-view')?.classList.contains('active'),{timeout:10000});

// Return to map and verify export produces a download.
await page.goto('http://127.0.0.1:8000/index.html#map',{waitUntil:'domcontentloaded'});
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
