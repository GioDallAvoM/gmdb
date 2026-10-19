#!/usr/bin/env python3
"""Costruisce la copia pubblica di Gmdb (sola lettura) per Cloudflare Pages.

Uso: python3 build.py <pagina_artifact.html> <cartella_export_db> <cartella_uscita>
- pagina_artifact.html: la pagina Gmdb letta da claude.ai (index.html dell'artifact)
- cartella_export_db: contiene le sottocartelle film/ e ext/ con un JSON per titolo
  (come le salva ArtifactData list con out_dir)
- cartella_uscita: dove scrivere index.html
"""
import json, os, sys, glob, datetime

src, dbdir, out = sys.argv[1:4]
s = open(src, encoding="utf-8").read()

def load(coll):
    res = {}
    for p in sorted(glob.glob(os.path.join(dbdir, coll, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        body = d
        res[os.path.splitext(os.path.basename(p))[0]] = body
    return res

snap = {"film": load("film"), "ext": load("ext"),
        "data": datetime.date.today().isoformat()}

# 1) dati congelati, prima dello script principale
marker = "<script>\nconst BASE = ["
assert s.count(marker) == 1, "struttura della pagina cambiata: manca const BASE"
inject = "<script>window.GMDB_SNAPSHOT=" + json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";</script>\n"
s = s.replace(marker, inject + marker)

# 2) senza claude.ai, carica i dati congelati invece dell'archivio
old = '  if(!cl?.use){ dbState="off"; render(); return; }'
assert s.count(old) == 1, "struttura della pagina cambiata: manca il caricamento dati"
new = ('  if(!cl?.use){ const S0=window.GMDB_SNAPSHOT; if(S0){ for(const [k,v] of Object.entries(S0.ext||{})) EXT[k]={...(EXT[k]||{}),...v}; '
       'VOTI=S0.film||{}; dbState="snap"; } else dbState="off"; render(); if(S.open) renderSheet(); return; }')
s = s.replace(old, new)

# 3) nota in scheda: copia in sola lettura
s = s.replace('${dbState==="off"?"I voti per categoria non si possono caricare in questa vista.":"Stai guardando la scheda in sola lettura."}',
              '${dbState==="off"?"I voti per categoria non si possono caricare in questa vista.":dbState==="snap"?"Copia in sola lettura di Gmdb.":"Stai guardando la scheda in sola lettura."}')

os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(s)
print("ok:", len(snap["film"]), "schede voti,", len(snap["ext"]), "voti esterni ->", os.path.join(out, "index.html"))
