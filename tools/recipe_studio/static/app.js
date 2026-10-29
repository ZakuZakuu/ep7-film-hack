"use strict";
const $ = id => document.getElementById(id);
const names = ["黄 / 金", "橙", "红", "玫红", "洋红", "紫", "蓝", "天蓝", "青", "青绿", "绿", "黄绿"];
const colors = ["#e7c446","#e7983b","#dd5f50","#d96e94","#c96ac8","#9e78d4","#6384db","#65b4e4","#58d0d0","#55b39b","#88c764","#b8ca5b"];
let modelLabel="近似后备模型", token, cal, ready = false, recipe, timer, previewSeq = 0, report = null, editing = 0;
function neutral() { return {format:"ep7-film-recipe-v1",name:"新配方",description:"",settings:{hue:Array(12).fill(0),saturation:Array(12).fill(0),lightness:Array(12).fill(0),tone:{shadows:0,midtones:0,highlights:0},shading:0},recommendations:{white_balance:"",wb_shift:"",exposure_compensation:""}}; }
function status(text) { $("status").textContent = text; }
async function api(path, options = {}) {
  options.headers = {...options.headers, "X-Studio-Token":token};
  const res = await fetch(path, options);
  if (!res.ok) { let msg; try { msg = (await res.json()).error; } catch { msg = `请求失败 (${res.status})`; } throw Error(msg); }
  return res;
}
function post(path, body) { return api(path, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); }
function save(name, obj) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)+"\n"],{type:"application/json"}));
  const a = document.createElement("a"); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function metadata() {
  recipe.name = $("name").value; recipe.description = $("description").value;
  for (const k of Object.keys(recipe.recommendations)) recipe.recommendations[k] = $(k).value;
  return recipe;
}
function slider(parent, label, min, max, value, update) {
  const row = document.createElement("label"); row.className="slider";
  const title = document.createElement("span"); title.textContent=label;
  const input = document.createElement("input"); input.type="range"; input.min=min; input.max=max; input.step=1; input.value=value;
  const out = document.createElement("output"); out.textContent=value;
  input.addEventListener("input",()=>{out.textContent=input.value;update(Number(input.value));editing++;schedule();});
  input.addEventListener("dblclick",()=>{if(Number(input.value)===0)return;input.value=0;out.textContent=0;update(0);editing++;schedule();});
  row.append(title,input,out);parent.append(row);
}
function controls() {
  $("name").value=recipe.name; $("description").value=recipe.description;
  for (const k of Object.keys(recipe.recommendations)) $(k).value=recipe.recommendations[k];
  $("sectors").replaceChildren(); $("other").replaceChildren();
  names.forEach((name,i)=>{
    const box=document.createElement("div");box.className="sector";
    const h=document.createElement("h3");const dot=document.createElement("span");
    // Fixed local palette, not input-supplied CSS.
    dot.style.backgroundColor=colors[i];h.append(dot,document.createTextNode(`${i+1}. ${name}`));box.append(h);
    for(const [axis,label] of [["hue","色相 H"],["saturation","饱和 S"],["lightness","明度 L"]]) slider(box,label,-cal.limits[axis],cal.limits[axis],recipe.settings[axis][i],v=>recipe.settings[axis][i]=v);
    $("sectors").append(box);
  });
  for(const [k,label] of [["shadows","阴影"],["midtones","中间调"],["highlights","高光"]]) slider($("other"),label,-cal.limits.tone,cal.limits.tone,recipe.settings.tone[k],v=>recipe.settings.tone[k]=v);
  slider($("other"),"暗角",-cal.limits.shading,cal.limits.shading,recipe.settings.shading,v=>recipe.settings.shading=v);
}
function schedule() { clearTimeout(timer);timer=setTimeout(preview,100); }
let rendering=false, pending=false, effectURL=null;
async function preview() {
  if(!ready)return;
  if(rendering){pending=true;return;}
  rendering=true;const seq=++previewSeq;
  try {
    const res=await post("/api/preview",metadata());const blob=await res.blob();
    if(seq===previewSeq){const old=effectURL;effectURL=URL.createObjectURL(blob);$("effect").src=effectURL;$("effect").style.visibility="visible";if(old)URL.revokeObjectURL(old);status("预览已更新 · "+modelLabel);}
  }catch(e){status(e.message);}finally{rendering=false;if(pending){pending=false;preview();}}
}
$("split").oninput=()=>{const v=Number($("split").value);$("original").style.clipPath=`inset(0 ${100-v}% 0 0)`;$("divider").style.left=`${v}%`;};
$("base").onchange=async()=>{
  if(!$("base").files[0])return;
  try{status("正在本机解码…");const form=new FormData();form.append("file",$("base").files[0]);const data=await(await api("/api/upload/base",{method:"POST",body:form})).json();$("decode").textContent=data.info.warning+" · "+data.info.decoder;$("original").src="/api/base.png?v="+data.revision;$("original").style.visibility="visible";$("empty").hidden=true;$("divider").hidden=false;ready=true;editing++;$("fit").disabled=false;schedule();}catch(e){status(e.message);}
};
$("target-file").onchange=async()=>{
  if(!$("target-file").files[0])return;
  try{const form=new FormData();form.append("file",$("target-file").files[0]);await api("/api/upload/"+($("fit-mode").value==="lut-only"?"lut":$("fit-mode").value),{method:"POST",body:form});editing++;status("目标已载入；确认方式与文件对应后开始拟合");}catch(e){status(e.message);}
};
$("fit-mode").onchange=()=>{$("fit").disabled=!(ready||$("fit-mode").value==="lut-only");$("target-file").value="";status("拟合方式已更改，请重新载入对应目标文件");};
$("save").onclick=async()=>{try{const valid=await(await post("/api/validate",metadata())).json();save("ep7-recipe.json",valid);}catch(e){status(e.message);}};
$("recipe-file").onchange=async()=>{try{const f=$("recipe-file").files[0];if(!f)return;if(f.size>100000)throw Error("配方文件过大");recipe=await(await api("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},body:await f.text()})).json();editing++;controls();schedule();}catch(e){status(e.message);}};
for(const key of ["name","description","white_balance","wb_shift","exposure_compensation"]) $(key).addEventListener("input",()=>editing++);
$("reset").onclick=()=>{metadata();recipe.settings=neutral().settings;editing++;controls();schedule();};
$("save-report").onclick=()=>save("ep7-fit-report.json",report);
$("fit").onclick=async()=>{
  $("fit").disabled=true;const startEditing=editing;
  try{
    await post("/api/fit",{mode:$("fit-mode").value,recipe:metadata(),smoothness:Number($("smoothness").value),magnitude:Number($("magnitude").value),starts:Number($("starts").value)});status("拟合中；照片只在本机处理…");
    while(true){await new Promise(r=>setTimeout(r,600));const result=await(await api("/api/fit")).json();
      if(result.status==="error")throw Error(result.error);
      if(result.status!=="done"){status(`拟合中 · 已评估 ${result.evaluations||0} 次模型`);continue;}
      report=result.report;$("save-report").disabled=false;$("unsplit").disabled=!report.unsplit;$("comparison-link").hidden=!(ready&&["lut-only","lut"].includes($("fit-mode").value));
      const stats=report.validation_pixels||report.distribution_swatches_only;
      $("fit-summary").textContent=`拟合质量：${report.quality}\n${report.mode==="different-scene-distribution"?"统计色块":"保留像素验证"} ΔE00 均值 ${stats.mean_delta_e_2000.toFixed(2)}，P95 ${stats.p95_delta_e_2000.toFixed(2)}\n`+(report.wb_shift?JSON.stringify(report.wb_shift)+"\n":"")+report.warnings.join("\n")+"\n\n各色区：\n"+Object.entries(report.per_sector).map(([k,v])=>`${k}: ${v.mean_delta_e_2000===null?"未覆盖":v.mean_delta_e_2000.toFixed(2)} (${v.count} 点)`).join("\n");
      if(result.stale_input||editing!==startEditing){status("拟合期间输入已改变；结果仅保存在报告中，未覆盖当前配方");report.proposed_recipe=result.recipe;}else{recipe=result.recipe;editing++;controls();schedule();}break;
    }
  }catch(e){status(e.message);}finally{$("fit").disabled=!(ready||$("fit-mode").value==="lut-only");}
};
(async()=>{try{const data=await(await fetch("/api/config")).json();token=data.token;cal=data.calibration;modelLabel=data.model.label;document.querySelector(".badge").textContent=data.model.exact_hsl?"本地 · Workspace HSL":"本地 · 近似后备";recipe=neutral();controls();$("model-note").textContent=modelLabel;status("仅 LUT 可直接载入 LUT；基准照片可选");$("fit").disabled=false;}catch(e){status("初始化失败："+e.message);}})();

$("unsplit").onclick=()=>{if(report&&report.unsplit){recipe=report.unsplit.recipe;editing++;controls();schedule();}};
