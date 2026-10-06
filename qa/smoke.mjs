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
for(const phrase of ['45%','35%','20%','Current WASH conditions','Data sources']){
  if(!about.includes(phrase)) throw new Error('About section missing: '+phrase);
}

// Return to map and verify export produces a download.
await page.getByRole('button',{name:'Map'}).click();
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
