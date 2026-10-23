const $ = (s) => document.querySelector(s);
const state = { doctors: [], patients: [], appointments: [] };
const fmt = (value) => new Date(value).toLocaleString('it-IT', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' });
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options={}) {
  const response = await fetch('/api'+path, {headers:{'Content-Type':'application/json'}, ...options});
  const body = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(body.error || 'Si è verificato un errore.');
  return body;
}
function toast(message) { $('#toast').textContent=message; $('#toast').classList.remove('hidden'); setTimeout(()=>$('#toast').classList.add('hidden'),3000); }
function statusPill(status) { return `<span class="pill ${esc(status)}">${esc(status)}</span>`; }
function appointmentRow(a, actions=false) {
  return `<tr><td>${esc(a.patient_name)}</td><td>${esc(a.doctor_name)}<br><small style="color:#9099a7">${esc(a.specialty)}</small></td><td>${esc(fmt(a.appointment_date))}</td><td>${esc(a.reason)}</td><td>${statusPill(a.status)}</td>${actions?`<td><select class="action-select" aria-label="Cambia stato" data-id="${a.id}"><option value="">Cambia stato…</option>${['Prenotata','Confermata','Completata','Annullata'].filter(s=>s!==a.status).map(s=>`<option>${s}</option>`).join('')}</select> <button class="delete-btn" data-delete="${a.id}" title="Elimina" style="border:0;background:#fff0f1;color:#c54c5b;border-radius:6px;padding:7px">✕</button></td>`:''}</tr>`;
}
function fillTable(selector, rows, actions=false) {
  $(selector).innerHTML = rows.length ? rows.map(a=>appointmentRow(a,actions)).join('') : `<tr><td colspan="${actions?6:5}" class="empty">Nessun appuntamento trovato.</td></tr>`;
}
async function loadDashboard() {
  const [stats, appointments] = await Promise.all([api('/dashboard'),api('/appointments')]);
  $('#stat-total').textContent=stats.total_appointments;
  $('#stat-upcoming').textContent=stats.upcoming_appointments;
  $('#stat-confirmed').textContent=stats.confirmed_appointments;
  $('#stat-doctors').textContent=stats.doctors;
  const upcoming=appointments.filter(a=>a.status!=='Annullata').slice(0,5);
  fillTable('#recent-rows',upcoming);
}
async function loadAppointments() {
  const params = new URLSearchParams();
  if ($('#search').value.trim()) params.set('q',$('#search').value.trim());
  if ($('#status-filter').value!=='Tutte') params.set('status',$('#status-filter').value);
  const rows=await api('/appointments?'+params.toString());
  fillTable('#appointment-rows',rows,true);
}
async function loadDoctors() {
  state.doctors=await api('/doctors');
  $('#doctor-cards').innerHTML=state.doctors.map(d=>`<article class="doctor-card"><div class="doctor-avatar">${esc(d.name.split(' ').filter(Boolean).slice(-2).map(x=>x[0]).join(''))}</div><h3>${esc(d.name)}</h3><p>${esc(d.specialty)}</p><small>${esc(d.email)}</small></article>`).join('');
}
async function loadFormOptions() {
  [state.patients,state.doctors]=await Promise.all([api('/patients'),api('/doctors')]);
  $('#patient-id').innerHTML=state.patients.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('');
  $('#doctor-id').innerHTML=state.doctors.map(d=>`<option value="${d.id}">${esc(d.name)} · ${esc(d.specialty)}</option>`).join('');
}
function showView(name) {
  document.querySelectorAll('.view').forEach(v=>v.classList.add('hidden'));
  $(`#${name}-view`).classList.remove('hidden');
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
  $('#page-title').textContent={dashboard:'Panoramica',appointments:'Appuntamenti',doctors:'Medici'}[name];
  if(name==='dashboard') loadDashboard().catch(e=>toast(e.message));
  if(name==='appointments') loadAppointments().catch(e=>toast(e.message));
  if(name==='doctors') loadDoctors().catch(e=>toast(e.message));
}
async function openModal() {
  try {
    await loadFormOptions();
    const date=new Date(Date.now()+3600000); date.setMinutes(Math.ceil(date.getMinutes()/15)*15,0,0);
    $('#appointment-date').min=new Date().toISOString().slice(0,16);
    $('#appointment-date').value=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;
    $('#form-error').textContent='';
    $('#modal').classList.remove('hidden');
  } catch(e) { toast(e.message); }
}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
$('#new-appointment').addEventListener('click',openModal);
$('#new-from-dashboard').addEventListener('click',openModal);
$('#close-modal').addEventListener('click',()=>$('#modal').classList.add('hidden'));
$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')) $('#modal').classList.add('hidden');});
$('#search').addEventListener('input',()=>loadAppointments().catch(e=>toast(e.message)));
$('#status-filter').addEventListener('change',()=>loadAppointments().catch(e=>toast(e.message)));
$('#appointment-form').addEventListener('submit',async e=>{
  e.preventDefault(); $('#form-error').textContent='';
  const payload={patient_id:Number($('#patient-id').value),doctor_id:Number($('#doctor-id').value),appointment_date:$('#appointment-date').value,reason:$('#reason').value.trim()};
  try {
    await api('/appointments',{method:'POST',body:JSON.stringify(payload)});
    $('#modal').classList.add('hidden'); $('#reason').value='';
    toast('Appuntamento prenotato correttamente.');
    showView('appointments');
  } catch(err) { $('#form-error').textContent=err.message; }
});
$('#appointment-rows').addEventListener('change',async e=>{
  const id=e.target.dataset.id, status=e.target.value;
  if(!id||!status)return;
  try { await api(`/appointments/${id}`,{method:'PATCH',body:JSON.stringify({status})}); toast('Stato aggiornato.'); await loadAppointments(); await loadDashboard(); }
  catch(err){toast(err.message);}
});
$('#appointment-rows').addEventListener('click',async e=>{
  const id=e.target.dataset.delete;if(!id)return;
  if(!confirm('Eliminare definitivamente questo appuntamento?'))return;
  try {await api(`/appointments/${id}`,{method:'DELETE'});toast('Appuntamento eliminato.');await loadAppointments();await loadDashboard();}
  catch(err){toast(err.message);}
});
(async()=>{try{await api('/health');showView('dashboard');}catch(e){toast('Impossibile contattare il server. Avvia app.py.');}})();
