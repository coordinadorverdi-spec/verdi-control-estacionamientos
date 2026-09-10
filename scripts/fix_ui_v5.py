from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v5 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v5 -->
<script>
(function(){
  const platePattern=/^[A-Z0-9]{3}-[A-Z0-9]{3}$/;
  const specialWords=new Set(['bicicleta','patin','moto','bicimoto','trimoto']);
  function normalizeVehicleCode(){
    const input=$('code'), kind=$('kind'); if(!input)return '';
    let raw=String(input.value||'').trim().toUpperCase().replace(/\s+/g,'');
    const k=String(kind?.value||'').trim().toLowerCase();
    if(specialWords.has(k) && !platePattern.test(raw)) raw=k.toUpperCase();
    else raw=raw.replace(/[^A-Z0-9]/g,'');
    if(raw.length===6 && !platePattern.test(raw)) raw=raw.slice(0,3)+'-'+raw.slice(3);
    input.value=raw; return raw;
  }
  $('code')?.addEventListener('blur',normalizeVehicleCode);
  $('code')?.addEventListener('input',function(){this.value=this.value.toUpperCase()});

  async function persistEventParking(eventId, number){
    const n=parseInt(String(number||'').trim(),10); if(!eventId||!Number.isFinite(n))return;
    const p=(spaces||[]).find(x=>Number(x.space_number)===n); if(!p)return;
    const r=await sb.from('access_events').update({parking_space_id:p.id}).eq('id',eventId);
    if(r.error)console.warn('Cochera en movimiento:',r.error.message);
  }

  const oldMoveV4=window.move;
  window.move=async function(action,id){
    if(action==='entrada') normalizeVehicleCode();
    const parkingBefore=String($('spaces')?.value||'').trim();
    const codeBefore=String($('code')?.value||'').trim().toUpperCase();
    await oldMoveV4(action,id);
    if(action==='entrada' && parkingBefore){
      const code=codeBefore;
      const v=(vehicles||[]).find(x=>String(x.plate||x.code_label||'').toUpperCase()===code);
      if(v){
        const n=parseInt(parkingBefore.split(',')[0],10), p=(spaces||[]).find(x=>Number(x.space_number)===n);
        const data={authorized_parking_spaces:parkingBefore.split(',').map(x=>x.trim()).filter(Boolean).join(','),parking_basement:Number.isFinite(n)?(n<=43?'S1':n<=89?'S2':n<=136?'S3':n<=147?'S4':null):null,parking_required:true};
        if(p)data.parking_space_id=p.id;
        const r=await sb.from('vehicles').update(data).eq('id',v.id).eq('building_id',BUILDING_ID);
        if(r.error)console.warn('Persistencia cochera v5:',r.error.message);
        const latest=(events||[]).filter(e=>e.vehicle_id===v.id).slice(-1)[0];
        if(latest && latest.movement==='entrada') await persistEventParking(latest.id,n);
      }
      await load();
    }
  };

  const oldRenderV4=window.render;
  window.render=function(){oldRenderV4();
    const h=$('histList')?.closest('table')?.querySelector('thead tr');
    if(h){[...h.querySelectorAll('th')].forEach(th=>{if(th.textContent.trim()==='Trabajador')th.textContent='Cochera / sótano'});if(![...h.querySelectorAll('th')].some(th=>th.textContent.trim()==='Acciones')){const th=document.createElement('th');th.textContent='Acciones';h.appendChild(th)}}
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')