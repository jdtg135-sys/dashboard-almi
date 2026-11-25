import random, math, json
src = open('analisis/robustez_2027.py', encoding='utf-8').read()
exec(src[:src.index('import os\nN =')])
MESES = ["Nov","Dic","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct"]
SOL = [195,230,300,380,470,560,650,740,830,900,960,1000]
G = [1.0,1.0,1.1,1.2,1.3,1.4,1.5,1.5,1.5,1.5,1.5,1.5]
PROP = [0,0,15,30,50,70,90,100,125,150,175,200]
ENTRADA = {"TikTok":3,"Demand Gen":4,"YouTube":5,"Otras plataformas":7}
def cp(O): return min(O,100)*830 + max(0,min(O,200)-100)*1500
filas=[]
for i,(m,q,g,O) in enumerate(zip(MESES,SOL,G,PROP)):
    can=[]
    for n,cpa,s0,tope,brel,med,p in BASE:
        b=max(0.05,0.20*brel)
        t=tope if med else (0 if i<ENTRADA[n] else tope*min(1.0,0.25*(i-ENTRADA[n]+1)))
        can.append((n,curva(cpa/g,s0,b),t,b,PISO.get(n,0)))
    if i==0:
        pag=(430000,195,[]); inv=430000*30/1e6; sol_p=195
    else:
        r=presupuesto_para(q-O,can)
        assert r, (m,'no llega')
        inv=r[0]*30/1e6; sol_p=r[1]
        # solo pauta, para comparar
        r0=presupuesto_para(q,can); inv0=r0[0]*30/1e6
    prop_cost=cp(O)*30/1e6
    filas.append(dict(mes=m,total=q,pauta=round(sol_p),propios=O,inv_pauta=round(inv,1),inv_prop=round(prop_cost,1),inv_total=round(inv+prop_cost,1),solo_pauta=round(inv0,1) if i else round(inv,1)))
    print(filas[-1])
dm=sum(f['inv_total'] for f in filas[1:5]); tot=sum(f['inv_total'] for f in filas[1:]); tp=sum(f['solo_pauta'] for f in filas[1:])
print('dic-mar',round(dm,1),'dic-oct',round(tot,1),'solo pauta',round(tp,1))
json.dump(filas,open('analisis/calendario_propios_2027.json','w'),ensure_ascii=False,indent=1)
