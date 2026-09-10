from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v12 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v12 -->
<script>
(function(){
  function showAdmin(){
    try{
      const admin=$('admin');
      if(!admin || !canAdmin()) return;
      document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
      admin.classList.add('on');
      document.querySelectorAll('.tabs button[data-v]').forEach(x=>x.classList.remove('on'));
      const tab=document.querySelector('.tabs button[data-v="admin"]');
      if(tab) tab.classList.add('on');
    }catch(err){console.warn('showAdmin',err)}
  }
  function reinforceAdmin(){
    showAdmin();
    [0,50,150,400,800].forEach(ms=>setTimeout(showAdmin,ms));
  }
  const input=$('excelFile');
  if(input){
    // Intercept the change at document capture level. This is intentionally
    // earlier than any legacy handler that may switch back to REGISTRO.
    document.addEventListener('change',function(e){
      if(e.target!==input) return;
      const f=input.files?.[0];
      if(f){
        window.__verdiSelectedExcel=f;
        setMsg('importMsg','Archivo seleccionado: '+f.name,true);
      }
      reinforceAdmin();
      e.stopImmediatePropagation();
    },true);

    // Android browsers may return focus to the page after the file chooser.
    // Re-assert Administration at that point without opening the picker again.
    window.addEventListener('focus',function(){
      if(window.__verdiSelectedExcel || input.files?.[0]) reinforceAdmin();
    },true);

    input.addEventListener('click',function(e){
      // Do not prevent the native picker. Only keep the current view stable.
      showAdmin();
      e.stopPropagation();
    },true);
  }

  const importBtn=$('importExcel');
  if(importBtn){
    // The selected file remains in #excelFile; clicking this button is the
    // explicit action that starts the existing import routine.
    importBtn.addEventListener('click',function(){reinforceAdmin()},false);
  }
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
