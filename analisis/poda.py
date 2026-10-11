# -*- coding: utf-8 -*-
"""Candidatos a pausar: minimo 1.000 impresiones y CPA sobre 2x el de su campana."""
import os
import json, urllib.request, urllib.parse, collections, os, sys
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
c=json.load(open(os.path.join(BASE,"meta_credentials.json")))
T,ACT=c["access_token"],c["ad_account_id"]
P="offsite_conversion.fb_pixel_purchase"; L="offsite_conversion.fb_pixel_lead"
SINCE,UNTIL=sys.argv[1],sys.argv[2]
MIN_IMPR=1000

u=f"https://graph.facebook.com/v21.0/{ACT}/insights?"+urllib.parse.urlencode({
 "access_token":T,"level":"ad","limit":500,
 "fields":"campaign_name,adset_name,ad_name,ad_id,spend,impressions,clicks,ctr,actions",
 "time_range":json.dumps({"since":SINCE,"until":UNTIL})})
rows=[]
while u:
    d=json.load(urllib.request.urlopen(u)); rows+=d["data"]; u=d.get("paging",{}).get("next")

pc=collections.defaultdict(list)
for f in rows:
    cam=f.get("campaign_name","")
    if "Oct2026" not in cam: continue
    acc={a["action_type"]:float(a["value"]) for a in f.get("actions",[])}
    g=float(f.get("spend",0)); cv=acc.get(P,0) or acc.get(L,0)
    pc[cam[:2]].append({"n":f.get("ad_name",""),"id":f["ad_id"],"g":g,"cv":cv,
                        "i":int(f.get("impressions",0)),"ctr":float(f.get("ctr",0) or 0)})

podar=[]; total_rescate=0
for k in sorted(pc):
    ads=pc[k]; G=sum(a["g"] for a in ads); C=sum(a["cv"] for a in ads)
    cpa_camp=G/C if C else 0
    print(f"\n=== {k}  {G:,.0f} COP | {C:.0f} conv | CPA campana {cpa_camp:,.0f}")
    cands=[a for a in ads if a["i"]>=MIN_IMPR and (a["cv"]==0 or a["g"]/a["cv"] > 2*cpa_camp)]
    cands.sort(key=lambda a:-a["g"])
    for a in cands:
        cpa=a["g"]/a["cv"] if a["cv"] else None
        print(f"   PAUSAR {a['g']:>8,.0f} COP | {a['cv']:>3.0f} conv | "
              f"CPA {('sin conv' if cpa is None else format(cpa,',.0f')):>9} | "
              f"{a['i']:>7,} impr | CTR {a['ctr']:>4.2f}% | {a['n'][:42]}")
        podar.append({"id":a["id"],"nombre":a["n"],"campana":k,"gasto":a["g"],
                      "conv":a["cv"],"impr":a["i"]})
        total_rescate+=a["g"]
    if not cands: print("   (ninguno cumple el criterio)")

print(f"\n{len(podar)} anuncios a pausar | {total_rescate:,.0f} COP en 7 dias "
      f"({total_rescate/7:,.0f} COP/dia que se reasignan)")
json.dump(podar, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "a_podar.json"),"w"), ensure_ascii=False, indent=1)
