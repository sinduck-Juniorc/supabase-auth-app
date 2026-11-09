import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
try {
 const page=await browser.newPage();
 await page.setContent(await fs.readFile(path.join(root,'REPORT_ko.html'),'utf8'),{waitUntil:'domcontentloaded'});
 await page.evaluate(()=>document.fonts.ready);
 const layout=await page.evaluate(()=>[...document.querySelectorAll('.page')].map((p,i)=>{
   const c=p.querySelector('.content'); const last=c.lastElementChild;
   return {page:i+1,content_bottom:last.getBoundingClientRect().bottom-p.getBoundingClientRect().top,
     allowed_bottom:c.getBoundingClientRect().bottom-p.getBoundingClientRect().top,
     overflow:c.scrollHeight>c.clientHeight+1};
 }));
 await fs.writeFile(path.join(root,'verification/layout.json'),JSON.stringify(layout,null,2)+'\n');
 if(layout.some(p=>p.overflow))throw Error('페이지 본문 높이를 초과했습니다. layout.json을 확인하세요.');
 await page.pdf({path:path.join(root,'REPORT_ko.pdf'),format:'A4',printBackground:true,preferCSSPageSize:true});
 await page.locator('.page').first().screenshot({path:path.join(root,'verification/page-01.png')});
 await page.locator('.page').last().screenshot({path:path.join(root,'verification/page-10.png')});
 console.log('PDF 10쪽 원고와 첫·마지막 쪽 미리보기를 저장했습니다.');
}finally{await browser.close();}
