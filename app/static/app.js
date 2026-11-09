let currentPlan=null, currentProfile=null;
const $=s=>document.querySelector(s);
function toast(msg){const t=$("#toast");t.textContent=msg;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2200)}
function showCatalog(){document.querySelector("#food").scrollIntoView({behavior:"smooth"})}
function openModal(html){$("#modalBody").innerHTML=html;$("#modal").classList.remove("hidden")}
function closeModal(){$("#modal").classList.add("hidden")}

async function loadStats(){
 const r=await fetch("/api/stats"); const d=await r.json();
 $("#heroFoods").textContent=d.foods.toLocaleString(); $("#dataCount").textContent=d.foods.toLocaleString();
}
async function loadCatalog(q="",diet="all"){
 const r=await fetch(`/api/search?q=${encodeURIComponent(q)}&diet=${encodeURIComponent(diet)}`);
 const items=await r.json(); const c=$("#catalog"); c.innerHTML="";
 if(!items.length){c.innerHTML='<div class="loading">No foods found.</div>';return}
 items.forEach(x=>{const el=document.createElement("div");el.className="food";el.innerHTML=`
  <h4>${esc(x.name)}</h4><span class="tag">${esc(x.category)}</span><span class="tag">${esc(x.diet)}</span>
  <p><b>${x.calories}</b> kcal · ${x.protein}g protein · ${x.carbs}g carbs</p>
  <p>${esc(x.ingredients||"Ingredients not supplied")}</p>
  <button class="btn ghost" style="padding:7px 10px;margin-top:6px" onclick='recipe(${JSON.stringify(x.name)})'>View ingredients</button>`;c.appendChild(el)})
}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
async function recipe(name){
 const r=await fetch(`/api/recipe?name=${encodeURIComponent(name)}`);const x=await r.json();
 if(x.error){toast(x.error);return}
 openModal(`<div class="recipe"><span class="kicker">${esc(x.category)} · ${esc(x.diet)}</span><h2>${esc(x.name)}</h2>
 <div class="nutri"><div><b>${x.calories}</b><span>kcal</span></div><div><b>${x.protein}g</b><span>protein</span></div><div><b>${x.carbs}g</b><span>carbs</span></div><div><b>${x.fat}g</b><span>fat</span></div></div>
 <h4>Ingredients</h4><ul>${x.ingredients.map(i=>`<li>${esc(i)}</li>`).join("")||"<li>Ingredients are not available in the supplied record.</li>"}</ul>
 <p style="font-size:11px;color:#6b7771">Serving: ${esc(x.serving)}</p></div>`)
}
async function generatePlan(){
 const profile={age:+$("#age").value,height:+$("#height").value,weight:+$("#weight").value,diet:$("#diet").value,activity:$("#activity").value,goal:$("#goal").value};
 const r=await fetch("/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(profile)});
 const d=await r.json(); if(!r.ok){toast(d.error||"Could not generate plan");return}
 currentProfile=profile;currentPlan=d;localStorage.setItem("nutriai_profile",JSON.stringify(profile));localStorage.setItem("nutriai_plan",JSON.stringify(d));
 renderPlan(d); toast("Your new 7-day plan is ready.");
}
function renderPlan(p){
 $("#dashboard").classList.remove("hidden");$("#week").classList.remove("hidden");$("#grocery").classList.remove("hidden");
 $("#targetCal").textContent=p.target_calories.toLocaleString();let meals=p.days.flatMap(d=>d.meals);
 $("#mealCount").textContent=meals.length;$("#proteinAvg").textContent=Math.round(meals.reduce((s,m)=>s+m.protein,0)/7);$("#dataCount").textContent=$("#heroFoods").textContent;
 const g=$("#weekGrid");g.innerHTML="";
 p.days.forEach(day=>{const card=document.createElement("div");card.className="day-card";card.innerHTML=`<div class="day-head"><h3>Day ${day.day}</h3><span>${day.meals.reduce((s,m)=>s+m.calories,0).toFixed(0)} kcal</span></div>`;
 day.meals.forEach((m,i)=>{const row=document.createElement("div");row.className="meal";row.innerHTML=`<div class="meal-slot">${m.slot}</div><div><div class="meal-name">${esc(m.name)}</div><div class="meal-meta">${m.calories} kcal · ${m.protein}g protein</div></div><button class="swap" onclick='swapMeal(${day.day-1},${i})'>↻ Swap</button>`;card.appendChild(row)});g.appendChild(card)});
 buildGrocery(meals)
}
function buildGrocery(meals){
 const map={};meals.forEach(m=>String(m.ingredients||"").split(";").map(x=>x.trim()).filter(Boolean).forEach(i=>{const k=i.toLowerCase();map[k]=(map[k]||{name:i,count:0});map[k].count++}));
 const items=Object.values(map).sort((a,b)=>b.count-a.count);$("#groceryList").innerHTML=items.slice(0,60).map(x=>`<div class="grocery-item"><input type="checkbox"> ${esc(x.name)} <span style="color:#8a928d;font-size:9px">×${x.count}</span></div>`).join("");
}
async function swapMeal(dayIndex,mealIndex){
 const m=currentPlan.days[dayIndex].meals[mealIndex];const r=await fetch("/api/swap",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({current_name:m.name,slot:m.slot,profile:currentProfile,seed:Date.now()})});const x=await r.json();if(!r.ok){toast(x.error||"No alternative");return}
 currentPlan.days[dayIndex].meals[mealIndex]=x;localStorage.setItem("nutriai_plan",JSON.stringify(currentPlan));renderPlan(currentPlan);toast("Meal swapped.");
}
function regenerate(){generatePlan()}
function copyGrocery(){const text=[...document.querySelectorAll(".grocery-item")].map(x=>x.innerText).join("\n");navigator.clipboard.writeText(text);toast("Grocery list copied.")}
$("#profileForm").addEventListener("submit",e=>{e.preventDefault();generatePlan()});
$("#searchBox").addEventListener("input",e=>loadCatalog(e.target.value,$("#dietFilter").value));
$("#dietFilter").addEventListener("change",e=>loadCatalog($("#searchBox").value,e.target.value));
window.addEventListener("load",async()=>{await loadStats();await loadCatalog();const p=localStorage.getItem("nutriai_profile"),plan=localStorage.getItem("nutriai_plan");if(p){const x=JSON.parse(p);$("#age").value=x.age;$("#height").value=x.height;$("#weight").value=x.weight;$("#diet").value=x.diet;$("#activity").value=x.activity;$("#goal").value=x.goal}if(plan){currentProfile=JSON.parse(p||"{}");currentPlan=JSON.parse(plan);renderPlan(currentPlan)}});

async function logout(){await fetch("/api/logout",{method:"POST"});window.location.href="/login"}
