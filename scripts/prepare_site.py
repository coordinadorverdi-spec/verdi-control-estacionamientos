from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = '<select id="dept"><option value="">-- Seleccione Dpto. --</option></select>'
new = '<input id="dept" list="depts" inputmode="numeric" autocomplete="off" placeholder="Escriba o seleccione Dpto. (ej. 103)">'
s = s.replace(old, new, 1)

if 'exceljs@4.4.0' not in s:
    s = s.replace('</head>', '<script src="https://cdn.jsdelivr.net/npm/exceljs@4.4.0/dist/exceljs.min.js"></script>\n</head>', 1)

marker = '<!-- Simplified Excel patch -->'
if marker not in s:
    patch = r'''<!-- Simplified Excel patch -->
<script>
(function(){
  const v=x=>String(x==null?'':x).trim();
  const nd=x=>{let q=v(x).toUpperCase().replace(/^DPTO?\.?\s*/,'').replace(/[^0-9]/g,'');if(q.length===1)q='00'+q;if(q.length===2)q='0'+q;return q};
  const bv=x=>['SI','SÍ','YES','TRUE','1','X'].includes(v(x).toUpperCase());
  const tv=x=>{const q=v(x).toLowerCase();if(q.includes('moto'))return'moto';if(q.includes('bicic'))return'bicicleta';if(q.includes('otro'))return'otro';return'auto'};
  const rv=x=>{const q=v(x).toLowerCase();if(q.includes('inquilino')&&q.includes('extern'))return'inquilino_externo';if(q.includes('inquilino'))return'inquilino_dpto';if(q.includes('cochera')&&!q.includes('dpto'))return'propietario_cochera';if(q.includes('visita'))return'visita';return'propietario_dpto'};
  async function template(){
    if(!window.ExcelJS){alert('No se pudo cargar el generador Excel.');return}
    const wb=new ExcelJS.Workbook();wb.creator='VERDI';
    const ws=wb.addWorksheet('REGISTRO VEHICULAR');ws.views=[{state:'frozen',ySplit:1}];
    ws.addRow(['Placa / código','Dpto','Sótano','Persona asociada','Tipo','Relación','Cocheras','Visita frecuente','Observaciones']);
    ws.getRow(1).font={bold:true};ws.getRow(1).alignment={vertical:'middle',wrapText:true};ws.getRow(1).height=32;ws.autoFilter={from:'A1',to:'I501'};
    [18,12,12,30,16,34,18,20,40].forEach((w,i)=>ws.getColumn(i+1).width=w);
    for(let r=2;r<=501;r++){
      ws.getCell(r,3).dataValidation={type:'list',allowBlank:true,formulae:['"S1,S2,S3,S4"']};
      ws.getCell(r,5).dataValidation={type:'list',allowBlank:true,formulae:['"Auto,Moto,Bicicleta,Otro"']};
      ws.getCell(r,6).dataValidation={type:'list',allowBlank:true,formulae:['"Propietario de Dpto.,Inquilino de Dpto.,Propietario de cochera sin Dpto.,Inquilino externo,Visita"']};
      ws.getCell(r,8).dataValidation={type:'list',allowBlank:true,formulae:['"Sí,No"']};
    }
    ws.getRow(2).values=['Ejemplo: ABC123','306','S1','Nombre de la persona','Auto','Propietario de Dpto.','12,13','No',''];ws.getRow(2).font={italic:true};
    const buf=await wb.xlsx.writeBuffer();const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));a.download='VERDI_Formato_Unico_Vehiculos.xlsx';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }
  async function importOne(){
    const input=document.getElementById('excelFile');if(!input||!input.files||!input.files[0]){setMsg('importMsg','Seleccione un archivo Excel.');return}
    try{
      setMsg('importMsg','Procesando formato único...',true);const data=await input.files[0].arrayBuffer();const wb=XLSX.read(data,{type:'array'});const rows=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]],{defval:''});if(!rows.length){setMsg('importMsg','El archivo no contiene registros.');return}
      let created=0,updated=0,skipped=0;
      for(const row of rows){
        const plate=v(row['Placa / código']||row.placa_codigo||row.placa||row.codigo).toUpperCase();if(!plate||plate.startsWith('EJEMPLO:')){skipped++;continue}
        const dq=nd(row['Dpto']??row.dpto??row.departamento??'');let did=null;if(dq){let d=(depts||[]).find(x=>nd(x.code)===dq);if(d)did=d.id;else{const q=await sb.from('departments').select('id,code').eq('building_id',BUILDING_ID).ilike('code',dq).maybeSingle();if(q.error)throw q.error;if(q.data){did=q.data.id}else{const ins=await sb.from('departments').insert({code:dq,building_id:BUILDING_ID}).select().single();if(ins.error)throw ins.error;did=ins.data.id;depts.push(ins.data)}}}
        const person=v(row['Persona asociada']||row.persona_asociada||row.responsable);const relationship=rv(row['Relación']||row.relacion);const vehicle_type=tv(row['Tipo']||row.tipo);const frequent=bv(row['Visita frecuente']??row.visita_frecuente);const basement=v(row['Sótano']||row.sotano).toUpperCase();const spaces=v(row['Cocheras']||row.cocheras);const obs=v(row['Observaciones']||row.observaciones);const existing=(vehicles||[]).find(x=>(x.plate||x.code_label||'').toUpperCase()===plate);
        const payload={plate,code_label:plate,responsible_name:person||null,relationship,vehicle_type,department_id:did,is_frequent:frequent,parking_required:!!spaces,parking_basement:basement||null,authorized_parking_spaces:spaces||null,description:obs||null,building_id:BUILDING_ID};
        if(existing){const up=await sb.from('vehicles').update(payload).eq('id',existing.id).select().single();if(up.error)throw up.error;updated++}else{const ins=await sb.from('vehicles').insert(payload).select().single();if(ins.error)throw ins.error;created++}
      }
      await load();setMsg('importMsg',`Carga completada: ${created} nuevos, ${updated} actualizados, ${skipped} omitidos.`,true);
    }catch(e){console.error(e);setMsg('importMsg','Error en la carga: '+(e.message||e))}
  }
  document.addEventListener('click',e=>{if(e.target?.id==='template'){e.preventDefault();e.stopImmediatePropagation();template()}if(e.target?.id==='importExcel'){e.preventDefault();e.stopImmediatePropagation();importOne()}},true);
})();
</script>
'''
    s = s.replace('</body>', patch + '</body>')
p.write_text(s, encoding='utf-8')
