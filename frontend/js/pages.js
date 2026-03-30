/**
 * pages.js — All page renderers registered with the router.
 * Each page is a self-contained async function that renders into #content.
 */

// ================================================================== //
//  DASHBOARD                                                           //
// ================================================================== //
registerPage("#dashboard", async (el, title) => {
  title.textContent = "Dashboard";
  const stats = await Api.get("/dashboard/", { jaar: App.jaar });

  el.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi">
        <div class="label">Omzet (excl. BTW)</div>
        <div class="value">${eur(stats.omzet_excl_btw)}</div>
      </div>
      <div class="kpi">
        <div class="label">Inkoop (excl. BTW)</div>
        <div class="value">${eur(stats.inkoop_excl_btw)}</div>
      </div>
      <div class="kpi">
        <div class="label">Bruto winst</div>
        <div class="value ${stats.bruto_winst < 0 ? 'danger' : 'success'}">${eur(stats.bruto_winst)}</div>
      </div>
      <div class="kpi">
        <div class="label">Openstaande debiteuren</div>
        <div class="value ${stats.openstaande_debiteuren > 0 ? 'warning' : ''}">${eur(stats.openstaande_debiteuren)}</div>
      </div>
      <div class="kpi">
        <div class="label">Te betalen aan leveranciers</div>
        <div class="value ${stats.openstaande_crediteuren > 0 ? 'warning' : ''}">${eur(stats.openstaande_crediteuren)}</div>
      </div>
      <div class="kpi">
        <div class="label">BTW-saldo (af te dragen)</div>
        <div class="value ${stats.btw_saldo > 0 ? 'danger' : 'success'}">${eur(stats.btw_saldo)}</div>
      </div>
    </div>
    <div class="alert alert-info">
      Boekjaar <strong>${App.jaar}</strong> — Bedragen exclusief BTW tenzij anders vermeld.
    </div>`;
});

// ================================================================== //
//  RELATIES                                                            //
// ================================================================== //
registerPage("#relaties", async (el, title) => {
  title.textContent = "Relaties";
  const items = await Api.get("/relaties/");

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Klanten &amp; Leveranciers</h3>
        <button class="btn btn-primary btn-sm" onclick="openModal('modal-relatie')">+ Nieuw</button>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Naam</th><th>Type</th><th>Locatie</th>
                <th>BTW-nummer</th><th>Email</th><th>IBAN</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(r => `
                <tr>
                  <td><strong>${r.naam}</strong></td>
                  <td>${statusBadge(r.type === 'klant' ? 'verzonden' : r.type === 'leverancier' ? 'ontvangen' : 'betaald')}<span style="display:none">${r.type}</span></td>
                  <td>${r.locatie_type}</td>
                  <td>${r.btw_nummer || r.eu_btw_nummer || '—'}</td>
                  <td>${r.email || '—'}</td>
                  <td>${r.iban || '—'}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Relatie -->
    <div class="modal-overlay" id="modal-relatie">
      <div class="modal">
        <div class="modal-header">
          <h3>Nieuwe relatie</h3>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <form id="form-relatie" class="form-grid">
            <div class="form-group">
              <label>Type *</label>
              <select name="type" required>
                <option value="klant">Klant</option>
                <option value="leverancier">Leverancier</option>
                <option value="beide">Beide</option>
              </select>
            </div>
            <div class="form-group">
              <label>Naam *</label>
              <input name="naam" required />
            </div>
            <div class="form-group">
              <label>KvK-nummer</label>
              <input name="kvk_nummer" />
            </div>
            <div class="form-group">
              <label>BTW-nummer (NL)</label>
              <input name="btw_nummer" placeholder="NL000000000B01" />
            </div>
            <div class="form-group">
              <label>EU BTW-nummer</label>
              <input name="eu_btw_nummer" placeholder="DExxxxx / FRxxxxx" />
            </div>
            <div class="form-group">
              <label>Land</label>
              <input name="land" value="NL" maxlength="2" />
            </div>
            <div class="form-group">
              <label>Locatie type</label>
              <select name="locatie_type">
                <option value="NL">Nederland</option>
                <option value="EU">EU</option>
                <option value="buiten_EU">Buiten EU</option>
              </select>
            </div>
            <div class="form-group">
              <label>Adres</label>
              <input name="adres" />
            </div>
            <div class="form-group">
              <label>Postcode</label>
              <input name="postcode" />
            </div>
            <div class="form-group">
              <label>Plaats</label>
              <input name="plaats" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input name="email" type="email" />
            </div>
            <div class="form-group">
              <label>Telefoon</label>
              <input name="telefoon" />
            </div>
            <div class="form-group">
              <label>IBAN</label>
              <input name="iban" />
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-relatie')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveRelatie()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

async function saveRelatie() {
  const form = document.getElementById("form-relatie");
  const data = Object.fromEntries(new FormData(form));
  try {
    await Api.post("/relaties/", data);
    closeModal("modal-relatie");
    navigate("#relaties");
  } catch (err) {
    showAlert(err.error || "Fout bij opslaan", "danger");
  }
}

// ================================================================== //
//  VERKOOPFACTUREN                                                     //
// ================================================================== //
registerPage("#verkoopfacturen", async (el, title) => {
  title.textContent = "Verkoopfacturen";
  const items = await Api.get("/verkoopfacturen/");
  const klanten = await Api.get("/relaties/", { type: "klant" });
  const artikelen = await Api.get("/artikelen/");

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Verkoopfacturen</h3>
        <div class="flex flex-gap">
          <a class="btn btn-outline btn-sm" href="${Api.downloadUrl('/export/verkoopfacturen/csv')}">↓ CSV</a>
          <button class="btn btn-primary btn-sm" onclick="openModal('modal-verkoop')">+ Nieuwe factuur</button>
        </div>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nr.</th><th>Datum</th><th>Klant</th>
                <th class="text-right">Excl. BTW</th>
                <th class="text-right">BTW</th>
                <th class="text-right">Totaal</th>
                <th>Status</th><th>BTW type</th><th></th>
              </tr>
            </thead>
            <tbody>
              ${items.map(f => `
                <tr>
                  <td><strong>${f.factuurnummer}</strong></td>
                  <td>${nlDate(f.factuurdatum)}</td>
                  <td>${f.klant_naam}</td>
                  <td class="text-right">${eur(f.subtotaal)}</td>
                  <td class="text-right">${eur(f.btw_totaal)}</td>
                  <td class="text-right"><strong>${eur(f.totaal)}</strong></td>
                  <td>${statusBadge(f.status)}</td>
                  <td><span class="badge badge-blue">${f.btw_type}</span></td>
                  <td>
                    <button class="btn btn-outline btn-sm"
                      onclick="updateVerkoopStatus(${f.id}, '${f.status}')">Betaalstatus</button>
                  </td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal nieuwe verkoopfactuur -->
    <div class="modal-overlay" id="modal-verkoop">
      <div class="modal" style="width:min(900px,96vw)">
        <div class="modal-header">
          <h3>Nieuwe verkoopfactuur</h3>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <form id="form-verkoop" class="form-grid">
            <div class="form-group">
              <label>Klant</label>
              <select name="klant_id" onchange="vulKlantGegevens(this)">
                <option value="">— kies klant —</option>
                ${klanten.map(k => `<option value="${k.id}" data-naam="${k.naam}" data-adres="${k.adres || ''}" data-btw="${k.btw_nummer || k.eu_btw_nummer || ''}">${k.naam}</option>`).join("")}
              </select>
            </div>
            <div class="form-group">
              <label>Klantnaam *</label>
              <input name="klant_naam" id="inp-klant-naam" required />
            </div>
            <div class="form-group">
              <label>Adres</label>
              <input name="klant_adres" id="inp-klant-adres" />
            </div>
            <div class="form-group">
              <label>BTW-nummer klant</label>
              <input name="klant_btw_nummer" id="inp-klant-btw" />
            </div>
            <div class="form-group">
              <label>Factuurdatum *</label>
              <input name="factuurdatum" type="date" value="${today()}" required />
            </div>
            <div class="form-group">
              <label>Vervaldatum *</label>
              <input name="vervaldatum" type="date" value="${daysFromToday(30)}" required />
            </div>
            <div class="form-group">
              <label>BTW type</label>
              <select name="btw_type">
                <option value="NL">Nederland (NL)</option>
                <option value="EU_B2B">EU B2B (verlegd)</option>
                <option value="EU_B2C">EU B2C (OSS)</option>
                <option value="export">Export buiten EU (0%)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Betalingskenmerk</label>
              <input name="betalingskenmerk" />
            </div>
            <div class="form-group full">
              <label>Notities</label>
              <textarea name="notities" rows="2"></textarea>
            </div>
          </form>

          <div class="mt-2">
            <h4 style="margin-bottom:10px;font-size:13px">Factuurregels</h4>
            <div class="line-editor">
              <table id="tbl-regels">
                <thead>
                  <tr>
                    <th style="width:30%">Omschrijving</th>
                    <th style="width:10%">Aantal</th>
                    <th style="width:12%">Prijs excl.</th>
                    <th style="width:10%">BTW</th>
                    <th style="width:10%">BTW €</th>
                    <th style="width:12%">Totaal excl.</th>
                    <th style="width:12%">Totaal incl.</th>
                    <th style="width:4%"></th>
                  </tr>
                </thead>
                <tbody id="regels-body"></tbody>
                <tfoot>
                  <tr>
                    <td colspan="5" class="text-right">Subtotaal</td>
                    <td id="ft-excl" class="text-right">€ 0,00</td>
                    <td id="ft-incl" class="text-right">€ 0,00</td>
                    <td></td>
                  </tr>
                  <tr>
                    <td colspan="5" class="text-right">BTW totaal</td>
                    <td id="ft-btw" class="text-right" colspan="2">€ 0,00</td>
                    <td></td>
                  </tr>
                  <tr>
                    <td colspan="5" class="text-right"><strong>Totaal te betalen</strong></td>
                    <td id="ft-tot" class="text-right" colspan="2"><strong>€ 0,00</strong></td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
              <div class="line-add">
                <button class="btn btn-outline btn-sm" onclick="addRegel(${JSON.stringify(artikelen).replace(/"/g, '&quot;')})">+ Regel toevoegen</button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-verkoop')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveVerkoopfactuur()">Factuur aanmaken</button>
        </div>
      </div>
    </div>

    <!-- Modal betaalstatus -->
    <div class="modal-overlay" id="modal-betaal">
      <div class="modal" style="width:360px">
        <div class="modal-header"><h3>Betaalstatus bijwerken</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <input type="hidden" id="betaal-fid" />
          <div class="form-group mt-1">
            <label>Status</label>
            <select id="betaal-status">
              <option value="verzonden">Verzonden</option>
              <option value="betaald">Betaald</option>
              <option value="deels_betaald">Deels betaald</option>
              <option value="verlopen">Verlopen</option>
              <option value="gecrediteerd">Gecrediteerd</option>
            </select>
          </div>
          <div class="form-group mt-1">
            <label>Betaald bedrag (€)</label>
            <input type="number" id="betaal-bedrag" step="0.01" />
          </div>
          <div class="form-group mt-1">
            <label>Betalingsdatum</label>
            <input type="date" id="betaal-datum" value="${today()}" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-betaal')">Annuleren</button>
          <button class="btn btn-success" onclick="saveBetaalStatus()">Opslaan</button>
        </div>
      </div>
    </div>`;

  // Add initial empty line
  addRegel(artikelen);
});

function vulKlantGegevens(sel) {
  const opt = sel.options[sel.selectedIndex];
  document.getElementById("inp-klant-naam").value  = opt.dataset.naam  || "";
  document.getElementById("inp-klant-adres").value = opt.dataset.adres || "";
  document.getElementById("inp-klant-btw").value   = opt.dataset.btw   || "";
}

let _regelIdx = 0;
function addRegel(artikelen = []) {
  const idx = _regelIdx++;
  const tbody = document.getElementById("regels-body");
  if (!tbody) return;
  const row = document.createElement("tr");
  row.id = `regel-${idx}`;
  row.innerHTML = `
    <td>
      <select onchange="vulArtikelRegel(this, ${idx}, ${JSON.stringify(artikelen).replace(/"/g, '&quot;')})"
              style="width:100%;border:none;background:transparent;font-size:12px">
        <option value="">— vrij —</option>
        ${artikelen.map(a => `<option value="${a.id}" data-prijs="${a.verkoop_prijs||0}" data-btw="${a.btw_tarief}">${a.naam}</option>`).join("")}
      </select>
      <input name="omschrijving_${idx}" placeholder="Omschrijving" style="margin-top:2px;border:none;background:transparent;width:100%;font-size:12px" />
    </td>
    <td><input type="number" name="hoeveelheid_${idx}" value="1" min="0" step="0.01" onchange="herbereken(${idx})" style="width:60px" /></td>
    <td><input type="number" name="prijs_${idx}" value="0.00" step="0.01" onchange="herbereken(${idx})" style="width:70px" /></td>
    <td>
      <select name="btw_${idx}" onchange="herbereken(${idx})">
        <option value="21%">21%</option>
        <option value="9%">9%</option>
        <option value="0%">0%</option>
        <option value="vrij">Vrij</option>
        <option value="verlegd">Verlegd</option>
      </select>
    </td>
    <td id="btw-euros-${idx}">€ 0,00</td>
    <td id="excl-${idx}">€ 0,00</td>
    <td id="incl-${idx}">€ 0,00</td>
    <td><button class="btn btn-danger btn-sm" onclick="document.getElementById('regel-${idx}').remove();updateTotals()">×</button></td>`;
  tbody.appendChild(row);
}

function vulArtikelRegel(sel, idx) {
  const opt = sel.options[sel.selectedIndex];
  const prijs = parseFloat(opt.dataset.prijs || 0);
  const btw   = opt.dataset.btw || "21%";
  const p = document.querySelector(`[name="prijs_${idx}"]`);
  const b = document.querySelector(`[name="btw_${idx}"]`);
  if (p) p.value = prijs.toFixed(2);
  if (b) b.value = btw;
  herbereken(idx);
}

const BTW_RATES = { "21%": 0.21, "9%": 0.09, "0%": 0, "vrij": 0, "verlegd": 0 };

function herbereken(idx) {
  const aantal = parseFloat(document.querySelector(`[name="hoeveelheid_${idx}"]`)?.value || 0);
  const prijs  = parseFloat(document.querySelector(`[name="prijs_${idx}"]`)?.value || 0);
  const btw    = document.querySelector(`[name="btw_${idx}"]`)?.value || "21%";
  const rate   = BTW_RATES[btw] || 0;
  const excl   = aantal * prijs;
  const btwEur = excl * rate;
  const incl   = excl + btwEur;
  const fmt = v => `€ ${v.toFixed(2).replace(".", ",")}`;
  const e = id => document.getElementById(id);
  if (e(`excl-${idx}`))      e(`excl-${idx}`).textContent      = fmt(excl);
  if (e(`incl-${idx}`))      e(`incl-${idx}`).textContent      = fmt(incl);
  if (e(`btw-euros-${idx}`)) e(`btw-euros-${idx}`).textContent = fmt(btwEur);
  updateTotals();
}

function updateTotals() {
  let totExcl = 0, totBtw = 0;
  document.querySelectorAll("#regels-body tr").forEach(row => {
    const idx = row.id.replace("regel-", "");
    const aantal = parseFloat(document.querySelector(`[name="hoeveelheid_${idx}"]`)?.value || 0);
    const prijs  = parseFloat(document.querySelector(`[name="prijs_${idx}"]`)?.value || 0);
    const btw    = document.querySelector(`[name="btw_${idx}"]`)?.value || "21%";
    const excl   = aantal * prijs;
    totExcl += excl;
    totBtw  += excl * (BTW_RATES[btw] || 0);
  });
  const fmt = v => `€ ${v.toFixed(2).replace(".", ",")}`;
  const e = id => document.getElementById(id);
  if (e("ft-excl")) e("ft-excl").textContent = fmt(totExcl);
  if (e("ft-btw"))  e("ft-btw").textContent  = fmt(totBtw);
  if (e("ft-incl")) e("ft-incl").textContent = fmt(totExcl);
  if (e("ft-tot"))  e("ft-tot").textContent  = fmt(totExcl + totBtw);
}

async function saveVerkoopfactuur() {
  const form = document.getElementById("form-verkoop");
  const formData = Object.fromEntries(new FormData(form));

  const regels = [];
  document.querySelectorAll("#regels-body tr").forEach(row => {
    const idx = row.id.replace("regel-", "");
    const omschr = document.querySelector(`[name="omschrijving_${idx}"]`)?.value || "";
    const aantal = parseFloat(document.querySelector(`[name="hoeveelheid_${idx}"]`)?.value || 0);
    const prijs  = parseFloat(document.querySelector(`[name="prijs_${idx}"]`)?.value || 0);
    const btw    = document.querySelector(`[name="btw_${idx}"]`)?.value || "21%";
    if (prijs > 0 || omschr) {
      regels.push({ omschrijving: omschr, hoeveelheid: aantal, eenheidsprijs: prijs, btw_tarief: btw });
    }
  });

  if (!regels.length) { showAlert("Voeg minimaal één factuurregel toe.", "warning"); return; }

  try {
    const res = await Api.post("/verkoopfacturen/", { ...formData, regels });
    closeModal("modal-verkoop");
    showAlert(`Factuur ${res.factuurnummer} aangemaakt.`, "success");
    navigate("#verkoopfacturen");
  } catch (err) {
    showAlert(err.error || "Fout bij aanmaken factuur", "danger");
  }
}

function updateVerkoopStatus(fid, currentStatus) {
  document.getElementById("betaal-fid").value    = fid;
  document.getElementById("betaal-status").value = currentStatus;
  openModal("modal-betaal");
}

async function saveBetaalStatus() {
  const fid    = document.getElementById("betaal-fid").value;
  const status = document.getElementById("betaal-status").value;
  const bedrag = document.getElementById("betaal-bedrag").value;
  const datum  = document.getElementById("betaal-datum").value;
  try {
    await Api.patch(`/verkoopfacturen/${fid}/status`,
      { status, betaald_bedrag: bedrag ? parseFloat(bedrag) : null, betalingsdatum: datum || null });
    closeModal("modal-betaal");
    navigate("#verkoopfacturen");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  INKOOPFACTUREN                                                      //
// ================================================================== //
registerPage("#inkoopfacturen", async (el, title) => {
  title.textContent = "Inkoopfacturen";
  const items = await Api.get("/inkoopfacturen/");
  const leveranciers = await Api.get("/relaties/", { type: "leverancier" });

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Inkoopfacturen</h3>
        <div class="flex flex-gap">
          <a class="btn btn-outline btn-sm" href="${Api.downloadUrl('/export/inkoopfacturen/csv')}">↓ CSV</a>
          <button class="btn btn-primary btn-sm" onclick="openModal('modal-inkoop')">+ Nieuw</button>
        </div>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Ref</th><th>Datum</th><th>Leverancier</th>
                  <th class="text-right">Excl. BTW</th>
                  <th class="text-right">BTW</th>
                  <th class="text-right">Totaal</th>
                  <th>Status</th><th></th></tr>
            </thead>
            <tbody>
              ${items.map(f => `
                <tr>
                  <td>${f.referentie || f.leverancier_factuur_nr || '—'}</td>
                  <td>${nlDate(f.factuurdatum)}</td>
                  <td>${f.leverancier_naam}</td>
                  <td class="text-right">${eur(f.subtotaal)}</td>
                  <td class="text-right">${eur(f.btw_bedrag)}</td>
                  <td class="text-right"><strong>${eur(f.totaal)}</strong></td>
                  <td>${statusBadge(f.status)}</td>
                  <td><button class="btn btn-outline btn-sm" onclick="updateInkoopStatus(${f.id}, '${f.status}')">Status</button></td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal inkoop -->
    <div class="modal-overlay" id="modal-inkoop">
      <div class="modal">
        <div class="modal-header"><h3>Nieuwe inkoopfactuur</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <form id="form-inkoop" class="form-grid">
            <div class="form-group">
              <label>Leverancier</label>
              <select name="leverancier_id" onchange="vulLeverancier(this)">
                <option value="">— kies leverancier —</option>
                ${leveranciers.map(l => `<option value="${l.id}" data-naam="${l.naam}">${l.naam}</option>`).join("")}
              </select>
            </div>
            <div class="form-group">
              <label>Leverancier naam *</label>
              <input name="leverancier_naam" id="inp-lev-naam" required />
            </div>
            <div class="form-group">
              <label>Lev. factuurnummer</label>
              <input name="leverancier_factuur_nr" />
            </div>
            <div class="form-group">
              <label>Uw referentie</label>
              <input name="referentie" />
            </div>
            <div class="form-group">
              <label>Factuurdatum *</label>
              <input name="factuurdatum" type="date" value="${today()}" required />
            </div>
            <div class="form-group">
              <label>Vervaldatum *</label>
              <input name="vervaldatum" type="date" value="${daysFromToday(30)}" required />
            </div>
            <div class="form-group">
              <label>Bedrag excl. BTW *</label>
              <input name="subtotaal" type="number" step="0.01" required onchange="updateInkoopTotaal()" />
            </div>
            <div class="form-group">
              <label>BTW tarief</label>
              <select name="inkoop_btw_tarief" id="inkoop-btw-tarief" onchange="updateInkoopTotaal()">
                <option value="21%">21%</option>
                <option value="9%">9%</option>
                <option value="0%">0%</option>
                <option value="vrij">Vrijgesteld</option>
                <option value="verlegd">Verlegd</option>
              </select>
            </div>
            <div class="form-group">
              <label>BTW bedrag (€)</label>
              <input name="btw_bedrag" id="inkoop-btw-euro" type="number" step="0.01" value="0.00" />
            </div>
            <div class="form-group">
              <label>Totaal incl. BTW</label>
              <input name="totaal" id="inkoop-totaal" type="number" step="0.01" value="0.00" readonly />
            </div>
            <div class="form-group">
              <label>BTW type</label>
              <select name="btw_type">
                <option value="NL">Nederland</option>
                <option value="EU_B2B">EU B2B</option>
                <option value="import">Import (buiten EU)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Categorie</label>
              <select name="categorie">
                <option value="">— overig —</option>
                <option value="inkoop_goederen">Inkoop goederen</option>
                <option value="kantoorkosten">Kantoorkosten</option>
                <option value="autokosten">Autokosten</option>
                <option value="huur">Huur</option>
                <option value="marketing">Marketing</option>
                <option value="abonnementen">Abonnementen</option>
              </select>
            </div>
            <div class="form-group full">
              <label>Notities</label>
              <textarea name="notities" rows="2"></textarea>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-inkoop')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveInkoop()">Opslaan</button>
        </div>
      </div>
    </div>

    <!-- Modal inkoop status -->
    <div class="modal-overlay" id="modal-inkoop-status">
      <div class="modal" style="width:340px">
        <div class="modal-header"><h3>Status bijwerken</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <input type="hidden" id="inkoop-fid" />
          <div class="form-group mt-1">
            <label>Status</label>
            <select id="inkoop-status-sel">
              <option value="ontvangen">Ontvangen</option>
              <option value="goedgekeurd">Goedgekeurd</option>
              <option value="betaald">Betaald</option>
              <option value="deels_betaald">Deels betaald</option>
            </select>
          </div>
          <div class="form-group mt-1">
            <label>Betaald bedrag (€)</label>
            <input type="number" id="inkoop-betaal-bedrag" step="0.01" />
          </div>
          <div class="form-group mt-1">
            <label>Betalingsdatum</label>
            <input type="date" id="inkoop-betaal-datum" value="${today()}" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-inkoop-status')">Annuleren</button>
          <button class="btn btn-success" onclick="saveInkoopStatus()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

function vulLeverancier(sel) {
  const opt = sel.options[sel.selectedIndex];
  document.getElementById("inp-lev-naam").value = opt.dataset.naam || "";
}

function updateInkoopTotaal() {
  const subtotaal = parseFloat(document.querySelector("[name='subtotaal']")?.value || 0);
  const tarief = document.getElementById("inkoop-btw-tarief")?.value || "21%";
  const rate = BTW_RATES[tarief] || 0;
  const btw = subtotaal * rate;
  const totaal = subtotaal + btw;
  const e = id => document.getElementById(id);
  if (e("inkoop-btw-euro")) e("inkoop-btw-euro").value = btw.toFixed(2);
  if (e("inkoop-totaal"))   e("inkoop-totaal").value   = totaal.toFixed(2);
}

async function saveInkoop() {
  const form = document.getElementById("form-inkoop");
  const data = Object.fromEntries(new FormData(form));
  const tarief = data.inkoop_btw_tarief || "21%";
  const excl = parseFloat(data.subtotaal || 0);
  const rate = BTW_RATES[tarief] || 0;
  const btw  = parseFloat(data.btw_bedrag || excl * rate);

  const payload = {
    ...data,
    subtotaal: excl,
    btw_bedrag: btw,
    totaal: excl + btw,
    regels: [{
      omschrijving: data.categorie || "Inkoop",
      hoeveelheid: 1,
      eenheidsprijs: excl,
      btw_tarief: tarief,
    }],
  };
  try {
    await Api.post("/inkoopfacturen/", payload);
    closeModal("modal-inkoop");
    navigate("#inkoopfacturen");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

function updateInkoopStatus(fid, current) {
  document.getElementById("inkoop-fid").value          = fid;
  document.getElementById("inkoop-status-sel").value   = current;
  openModal("modal-inkoop-status");
}

async function saveInkoopStatus() {
  const fid    = document.getElementById("inkoop-fid").value;
  const status = document.getElementById("inkoop-status-sel").value;
  const bedrag = document.getElementById("inkoop-betaal-bedrag").value;
  const datum  = document.getElementById("inkoop-betaal-datum").value;
  try {
    await Api.patch(`/inkoopfacturen/${fid}/status`,
      { status, betaald_bedrag: bedrag ? parseFloat(bedrag) : null, betalingsdatum: datum || null });
    closeModal("modal-inkoop-status");
    navigate("#inkoopfacturen");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  KASBOEK                                                            //
// ================================================================== //
registerPage("#kasboek", async (el, title) => {
  title.textContent = "Kasboek / Bankboek";
  const items = await Api.get("/kasboek/", { jaar: App.jaar });

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Kasboek ${App.jaar}</h3>
        <div class="flex flex-gap">
          <a class="btn btn-outline btn-sm" href="${Api.downloadUrl('/export/kasboek/csv', { jaar: App.jaar })}">↓ CSV</a>
          <a class="btn btn-outline btn-sm" href="${Api.downloadUrl('/export/kasboek/qif', { jaar: App.jaar })}">↓ QIF (GnuCash)</a>
          <button class="btn btn-primary btn-sm" onclick="openModal('modal-kas')">+ Toevoegen</button>
        </div>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Datum</th><th>Type</th><th>Cat.</th>
                  <th>Omschrijving</th>
                  <th class="text-right">Bedrag</th>
                  <th>BTW</th></tr>
            </thead>
            <tbody>
              ${items.map(r => `
                <tr>
                  <td>${nlDate(r.datum)}</td>
                  <td>${r.rekening_type}</td>
                  <td><span class="badge ${r.categorie === 'ontvangst' ? 'badge-green' : 'badge-red'}">${r.categorie}</span></td>
                  <td>${r.omschrijving}</td>
                  <td class="text-right ${r.categorie === 'ontvangst' ? 'text-success' : 'text-danger'}">
                    ${r.categorie === 'uitgave' ? '-' : ''}${eur(r.bedrag)}</td>
                  <td>${r.btw_tarief} (${eur(r.btw_bedrag)})</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="modal-overlay" id="modal-kas">
      <div class="modal" style="width:460px">
        <div class="modal-header"><h3>Kasboekregel toevoegen</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <form id="form-kas" class="form-grid">
            <div class="form-group"><label>Datum *</label><input name="datum" type="date" value="${today()}" required /></div>
            <div class="form-group"><label>Rekening</label>
              <select name="rekening_type">
                <option value="bank">Bank</option>
                <option value="kas">Kas</option>
                <option value="pin">Pin</option>
              </select>
            </div>
            <div class="form-group"><label>Categorie *</label>
              <select name="categorie" required>
                <option value="ontvangst">Ontvangst</option>
                <option value="uitgave">Uitgave</option>
              </select>
            </div>
            <div class="form-group"><label>Bedrag (€) *</label><input name="bedrag" type="number" step="0.01" required /></div>
            <div class="form-group full"><label>Omschrijving *</label><input name="omschrijving" required /></div>
            <div class="form-group"><label>BTW tarief</label>
              <select name="btw_tarief">
                <option value="0%">0% (geen BTW)</option>
                <option value="21%">21%</option>
                <option value="9%">9%</option>
              </select>
            </div>
            <div class="form-group"><label>Tegenrekening (grootboek)</label><input name="tegenrekening" /></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-kas')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveKas()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

async function saveKas() {
  const form = document.getElementById("form-kas");
  const data = Object.fromEntries(new FormData(form));
  data.bedrag = parseFloat(data.bedrag);
  try {
    await Api.post("/kasboek/", data);
    closeModal("modal-kas");
    navigate("#kasboek");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  ACTIVA                                                              //
// ================================================================== //
registerPage("#activa", async (el, title) => {
  title.textContent = "Activaregister";
  const items = await Api.get("/activa/");

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Vaste Activa</h3>
        <button class="btn btn-primary btn-sm" onclick="openModal('modal-actief')">+ Nieuw actief</button>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Naam</th><th>Categorie</th><th>Aanschaf</th>
                  <th class="text-right">Aanschafwaarde</th>
                  <th class="text-right">Boekwaarde</th>
                  <th class="text-right">Afschr./jaar</th>
                  <th>Methode</th><th>Restjaren</th></tr>
            </thead>
            <tbody>
              ${items.map(a => {
                const elapsed = new Date().getFullYear() - new Date(a.aanschafdatum).getFullYear();
                const restjaren = Math.max(0, a.afschrijvingsjaren - elapsed);
                return `<tr>
                  <td><strong>${a.naam}</strong></td>
                  <td>${a.categorie || '—'}</td>
                  <td>${nlDate(a.aanschafdatum)}</td>
                  <td class="text-right">${eur(a.aanschafwaarde)}</td>
                  <td class="text-right">${eur(a.boekwaarde)}</td>
                  <td class="text-right">${eur(a.afschrijving_per_jaar)}</td>
                  <td>${a.afschrijvingsmethode}</td>
                  <td>${restjaren} jr</td>
                </tr>`;
              }).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="modal-overlay" id="modal-actief">
      <div class="modal">
        <div class="modal-header"><h3>Nieuw actief</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <form id="form-actief" class="form-grid">
            <div class="form-group"><label>Naam *</label><input name="naam" required /></div>
            <div class="form-group"><label>Categorie</label>
              <select name="categorie">
                <option value="computer">Computer / IT</option>
                <option value="auto">Auto</option>
                <option value="inventaris">Inventaris</option>
                <option value="machines">Machines</option>
                <option value="overig">Overig</option>
              </select>
            </div>
            <div class="form-group"><label>Aanschafdatum *</label><input name="aanschafdatum" type="date" value="${today()}" required /></div>
            <div class="form-group"><label>Aanschafwaarde (€) *</label><input name="aanschafwaarde" type="number" step="0.01" required /></div>
            <div class="form-group"><label>Restwaarde (€)</label><input name="restwaarde" type="number" step="0.01" value="0" /></div>
            <div class="form-group"><label>Afschrijvingsjaren</label><input name="afschrijvingsjaren" type="number" value="5" min="1" /></div>
            <div class="form-group"><label>Methode</label>
              <select name="afschrijvingsmethode">
                <option value="lineair">Lineair</option>
                <option value="degressief">Degressief</option>
              </select>
            </div>
            <div class="form-group full"><label>Omschrijving</label><textarea name="omschrijving" rows="2"></textarea></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-actief')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveActief()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

async function saveActief() {
  const form = document.getElementById("form-actief");
  const data = Object.fromEntries(new FormData(form));
  try {
    await Api.post("/activa/", data);
    closeModal("modal-actief");
    navigate("#activa");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  PLATFORM KOSTEN                                                     //
// ================================================================== //
registerPage("#platform", async (el, title) => {
  title.textContent = "Platform kosten";
  const items = await Api.get("/platform/", { jaar: App.jaar });

  el.innerHTML = `
    <div class="alert alert-info">
      Platform commissies (Bol.com, Etsy, Amazon, etc.) — niet-NL platforms kunnen
      <strong>omgekeerde heffing</strong> vereisen: u draagt dan zelf de BTW af.
    </div>
    <div class="card">
      <div class="card-header">
        <h3>Platform kosten ${App.jaar}</h3>
        <div class="flex flex-gap">
          <a class="btn btn-outline btn-sm" href="${Api.downloadUrl('/export/platform/csv', { jaar: App.jaar })}">↓ CSV</a>
          <button class="btn btn-primary btn-sm" onclick="openModal('modal-platform')">+ Toevoegen</button>
        </div>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Datum</th><th>Platform</th><th>Type</th><th>Omschrijving</th>
                  <th class="text-right">Excl. BTW</th>
                  <th class="text-right">BTW</th>
                  <th class="text-right">Totaal</th>
                  <th>Omg. heffing</th></tr>
            </thead>
            <tbody>
              ${items.map(p => `
                <tr>
                  <td>${nlDate(p.datum)}</td>
                  <td><strong>${p.platform}</strong></td>
                  <td>${p.type}</td>
                  <td>${p.omschrijving || '—'}</td>
                  <td class="text-right">${eur(p.bedrag_excl_btw)}</td>
                  <td class="text-right">${eur(p.btw_bedrag)}</td>
                  <td class="text-right">${eur(p.totaal)}</td>
                  <td>${p.omgekeerde_heffing ? '<span class="badge badge-orange">Ja</span>' : '—'}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="modal-overlay" id="modal-platform">
      <div class="modal">
        <div class="modal-header"><h3>Platform kost toevoegen</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <form id="form-platform" class="form-grid">
            <div class="form-group"><label>Datum *</label><input name="datum" type="date" value="${today()}" required /></div>
            <div class="form-group"><label>Platform *</label>
              <select name="platform">
                <option value="Bol.com">Bol.com</option>
                <option value="Etsy">Etsy</option>
                <option value="Amazon">Amazon</option>
                <option value="eBay">eBay</option>
                <option value="Marktplaats">Marktplaats</option>
                <option value="Shopify">Shopify</option>
                <option value="overig">Overig</option>
              </select>
            </div>
            <div class="form-group"><label>Type *</label>
              <select name="type">
                <option value="commissie">Commissie</option>
                <option value="abonnement">Abonnement</option>
                <option value="verzendkosten">Verzendkosten</option>
                <option value="reclame">Reclame</option>
                <option value="overig">Overig</option>
              </select>
            </div>
            <div class="form-group"><label>Bedrag excl. BTW (€) *</label>
              <input name="bedrag_excl_btw" type="number" step="0.01" required />
            </div>
            <div class="form-group"><label>BTW tarief</label>
              <select name="btw_tarief">
                <option value="21%">21%</option>
                <option value="0%">0%</option>
              </select>
            </div>
            <div class="form-group"><label>Omgekeerde heffing (niet-NL platform)</label>
              <select name="omgekeerde_heffing">
                <option value="false">Nee</option>
                <option value="true">Ja (verlegd)</option>
              </select>
            </div>
            <div class="form-group"><label>Factuur referentie</label><input name="factuur_referentie" /></div>
            <div class="form-group full"><label>Omschrijving</label><input name="omschrijving" /></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-platform')">Annuleren</button>
          <button class="btn btn-primary" onclick="savePlatform()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

async function savePlatform() {
  const form = document.getElementById("form-platform");
  const data = Object.fromEntries(new FormData(form));
  data.omgekeerde_heffing = data.omgekeerde_heffing === "true";
  try {
    await Api.post("/platform/", data);
    closeModal("modal-platform");
    navigate("#platform");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  BTW AANGIFTE                                                        //
// ================================================================== //
registerPage("#btw", async (el, title) => {
  title.textContent = "BTW Aangifte";
  const periodes = await Api.get("/btw/periodes");

  el.innerHTML = `
    <div class="alert alert-info">
      <strong>Let op:</strong> Dit systeem berekent uw BTW-aangifte op basis van uw facturen.
      Controleer altijd bij de Belastingdienst (Mijn Belastingdienst Zakelijk) vóór indiening.
      Bewaartermijn: <strong>7 jaar</strong> (art. 52 AWR).
    </div>

    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><h3>Nieuwe aangifte berekenen</h3></div>
      <div class="card-body">
        <form class="form-grid" id="form-btw">
          <div class="form-group">
            <label>Periode-ID</label>
            <input name="periode" placeholder="bijv. 2026-Q1" required />
          </div>
          <div class="form-group">
            <label>Type</label>
            <select name="type">
              <option value="kwartaal">Kwartaal</option>
              <option value="maand">Maand</option>
              <option value="jaar">Jaar</option>
            </select>
          </div>
          <div class="form-group">
            <label>Startdatum</label>
            <input name="startdatum" type="date" required />
          </div>
          <div class="form-group">
            <label>Einddatum</label>
            <input name="einddatum" type="date" required />
          </div>
        </form>
        <button class="btn btn-primary mt-1" onclick="berekenBtw()">Berekenen</button>
      </div>
    </div>

    <div id="btw-result"></div>

    <div class="card">
      <div class="card-header"><h3>Eerder berekende periodes</h3></div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Periode</th><th>Type</th><th>Van</th><th>Tot</th>
                  <th class="text-right">Omzet 21%</th>
                  <th class="text-right">Omzet 9%</th>
                  <th class="text-right">Voorbelasting</th>
                  <th class="text-right">Saldo BTW</th>
                  <th>Status</th></tr>
            </thead>
            <tbody>
              ${periodes.map(p => `
                <tr>
                  <td><strong>${p.periode}</strong></td>
                  <td>${p.type}</td>
                  <td>${nlDate(p.startdatum)}</td>
                  <td>${nlDate(p.einddatum)}</td>
                  <td class="text-right">${eur(p.omzet_21)}</td>
                  <td class="text-right">${eur(p.omzet_9)}</td>
                  <td class="text-right">${eur(p.voorbelasting_totaal)}</td>
                  <td class="text-right ${p.saldo_btw > 0 ? 'text-danger' : 'text-success'}">
                    <strong>${eur(p.saldo_btw)}</strong>
                  </td>
                  <td>${statusBadge(p.status)}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>`;
});

async function berekenBtw() {
  const form = document.getElementById("form-btw");
  const data = Object.fromEntries(new FormData(form));
  const result = document.getElementById("btw-result");
  result.innerHTML = spin();
  try {
    const aangifte = await Api.post("/btw/berekenen", data);
    result.innerHTML = renderBtwAangifte(aangifte);
  } catch (err) {
    result.innerHTML = `<div class="alert alert-danger">${err.error || "Fout bij berekening"}</div>`;
  }
}

function renderBtwAangifte(a) {
  const positive = a.saldo_btw > 0;
  return `
    <div class="card btw-report" style="margin-bottom:20px">
      <div class="card-header">
        <h3>BTW Aangifte — ${a.periode}</h3>
        <span class="badge ${positive ? 'badge-red' : 'badge-green'}">
          ${positive ? 'Te betalen' : 'Te vorderen'}: ${eur(Math.abs(a.saldo_btw))}
        </span>
      </div>
      <div class="card-body">
        <table>
          <thead><tr><th>Rubriek</th><th>Omschrijving</th><th class="text-right">Grondslag</th><th class="text-right">BTW</th></tr></thead>
          <tbody>
            <tr class="section-title"><td colspan="4">Af te dragen omzetbelasting</td></tr>
            <tr>
              <td>1a</td><td>Leveringen hoog tarief (21%)</td>
              <td class="text-right">${eur(a.omzet_21)}</td>
              <td class="text-right">${eur(a.btw_21_af)}</td>
            </tr>
            <tr>
              <td>1b</td><td>Leveringen laag tarief (9%)</td>
              <td class="text-right">${eur(a.omzet_9)}</td>
              <td class="text-right">${eur(a.btw_9_af)}</td>
            </tr>
            <tr>
              <td>3a</td><td>Export (0%) / nultarief</td>
              <td class="text-right">${eur(a.omzet_0)}</td>
              <td class="text-right">€ 0,00</td>
            </tr>
            <tr>
              <td>4a</td><td>Intra-EU B2B (verlegd)</td>
              <td class="text-right">${eur(a.omzet_verlegd)}</td>
              <td class="text-right">${eur(a.btw_verlegd_af)}</td>
            </tr>
            <tr>
              <td>5b</td><td>EU B2C / OSS</td>
              <td class="text-right">${eur(a.omzet_eu_b2c)}</td>
              <td class="text-right">${eur(a.btw_eu_b2c_af)}</td>
            </tr>
            <tr class="section-title"><td colspan="4">Voorbelasting (aftrekbare inkoop-BTW)</td></tr>
            <tr>
              <td>5b</td><td>Totale voorbelasting</td>
              <td class="text-right">—</td>
              <td class="text-right">- ${eur(a.voorbelasting_totaal)}</td>
            </tr>
            <tr class="${positive ? 'saldo-pos' : 'saldo-neg'}">
              <td colspan="3"><strong>${positive ? 'Te betalen aan Belastingdienst' : 'Te vorderen van Belastingdienst'}</strong></td>
              <td class="text-right"><strong>${eur(Math.abs(a.saldo_btw))}</strong></td>
            </tr>
          </tbody>
        </table>
        ${a.kor_actief ? '<div class="alert alert-warning mt-2">KOR actief — geen BTW verschuldigd.</div>' : ''}
        <p class="text-muted mt-1" style="font-size:12px">
          Aangifte periode: ${nlDate(a.startdatum)} t/m ${nlDate(a.einddatum)}
        </p>
      </div>
    </div>`;
}

// ================================================================== //
//  ARTIKELEN                                                           //
// ================================================================== //
registerPage("#artikelen", async (el, title) => {
  title.textContent = "Artikelen & Diensten";
  const items = await Api.get("/artikelen/");

  el.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h3>Artikelen & Diensten</h3>
        <button class="btn btn-primary btn-sm" onclick="openModal('modal-artikel')">+ Nieuw artikel</button>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Code</th><th>Naam</th><th>BTW</th>
                  <th class="text-right">Verkoopprijs</th>
                  <th class="text-right">Inkoopprijs</th>
                  <th class="text-right">Voorraad</th></tr>
            </thead>
            <tbody>
              ${items.map(a => `
                <tr>
                  <td>${a.code || '—'}</td>
                  <td><strong>${a.naam}</strong><br><small class="text-muted">${a.omschrijving || ''}</small></td>
                  <td><span class="badge badge-blue">${a.btw_tarief}</span></td>
                  <td class="text-right">${eur(a.verkoop_prijs)}</td>
                  <td class="text-right">${eur(a.inkoop_prijs)}</td>
                  <td class="text-right">${a.voorraad_bijhouden ? (a.voorraad_stand ?? 0) + ' ' + a.eenheid : '—'}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="modal-overlay" id="modal-artikel">
      <div class="modal">
        <div class="modal-header"><h3>Nieuw artikel / dienst</h3><button class="modal-close">&times;</button></div>
        <div class="modal-body">
          <form id="form-artikel" class="form-grid">
            <div class="form-group"><label>Code</label><input name="code" /></div>
            <div class="form-group"><label>Naam *</label><input name="naam" required /></div>
            <div class="form-group"><label>BTW tarief</label>
              <select name="btw_tarief">
                <option value="21%">21% (hoog)</option>
                <option value="9%">9% (laag)</option>
                <option value="0%">0% (nultarief)</option>
                <option value="vrij">Vrijgesteld</option>
                <option value="verlegd">Verlegd</option>
              </select>
            </div>
            <div class="form-group"><label>Verkoopprijs (excl. BTW)</label><input name="verkoop_prijs" type="number" step="0.01" /></div>
            <div class="form-group"><label>Inkoopprijs (excl. BTW)</label><input name="inkoop_prijs" type="number" step="0.01" /></div>
            <div class="form-group"><label>Eenheid</label>
              <select name="eenheid">
                <option value="stuk">Stuk</option>
                <option value="uur">Uur</option>
                <option value="dag">Dag</option>
                <option value="kg">Kg</option>
                <option value="m">Meter</option>
              </select>
            </div>
            <div class="form-group"><label>Voorraad bijhouden</label>
              <select name="voorraad_bijhouden">
                <option value="0">Nee</option>
                <option value="1">Ja</option>
              </select>
            </div>
            <div class="form-group"><label>Min. voorraad</label><input name="min_voorraad" type="number" value="0" /></div>
            <div class="form-group full"><label>Omschrijving</label><textarea name="omschrijving" rows="2"></textarea></div>
          </form>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeModal('modal-artikel')">Annuleren</button>
          <button class="btn btn-primary" onclick="saveArtikel()">Opslaan</button>
        </div>
      </div>
    </div>`;
});

async function saveArtikel() {
  const form = document.getElementById("form-artikel");
  const data = Object.fromEntries(new FormData(form));
  try {
    await Api.post("/artikelen/", data);
    closeModal("modal-artikel");
    navigate("#artikelen");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  INSTELLINGEN                                                        //
// ================================================================== //
registerPage("#instellingen", async (el, title) => {
  title.textContent = "Instellingen";
  const inst = await Api.get("/instellingen/");

  el.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>Bedrijfsgegevens & Instellingen</h3></div>
      <div class="card-body">
        <form id="form-inst" class="form-grid">
          ${Object.entries(inst).map(([k, v]) => `
            <div class="form-group">
              <label>${k.replace(/_/g, ' ')}</label>
              <input name="${k}" value="${v}" ${k === 'kor_actief' || k === 'btw_periode' ? 'placeholder="true/false of periode"' : ''} />
            </div>`).join("")}
        </form>
        <button class="btn btn-primary mt-2" onclick="saveInstellingen()">Opslaan</button>
      </div>
    </div>`;
});

async function saveInstellingen() {
  const form = document.getElementById("form-inst");
  const data = Object.fromEntries(new FormData(form));
  try {
    await Api.put("/instellingen/", data);
    App.instellingen = data;
    showAlert("Instellingen opgeslagen.", "success");
  } catch (err) {
    showAlert(err.error || "Fout", "danger");
  }
}

// ================================================================== //
//  Utility helpers                                                     //
// ================================================================== //
function today() {
  return new Date().toISOString().slice(0, 10);
}

function daysFromToday(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}
