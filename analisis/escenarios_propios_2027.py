import random, math, json, os
src = open('analisis/robustez_2027.py', encoding='utf-8').read()
exec(src[:src.index('import os\nN =')])
random.seed(11)
def cp(O): return min(O,100)*830 + max(0,min(O,200)-100)*1500 + max(0,O-200)*2200
todos = {n: True for n,_,_,_,_,med,_ in BASE if not med}
def need(g,b,fn,ft,O):
    can = armar(g,b,fn,ft,todos)
    r = presupuesto_para(1000-O, can)
    return None if not r else r[0]*30/1e6 + cp(O)*30/1e6
ESC = [("Pesimista", dict(g=1.0,b=.35,fn=1.4,ft=1.0), 100),
       ("Sin recuperar", dict(g=1.0,b=.29,fn=1.0,ft=1.0), 200),
       ("Base", dict(g=1.5,b=.20,fn=1.0,ft=1.0), 200),
       ("Optimista", dict(g=2.35,b=.10,fn=.7,ft=1.0), 200)]
out={'esc':[]}
for n,kw,O in ESC:
    a=need(kw['g'],kw['b'],kw['fn'],kw['ft'],0); c=need(kw['g'],kw['b'],kw['fn'],kw['ft'],O)
    out['esc'].append(dict(nombre=n,propios=O,solo_pauta=a,con_propios=c,cpa=(c*1e6/30/1000) if c else None))
    print(n,O,'solo pauta',a and round(a,1),'con propios',c and round(c,1),'cpa',c and round(c*1e6/30/1000))
# probabilidades a 51 M totales con O=200 (cumplimiento tri .5-1.3) y condicionales
N=3000
rs=[]
for _ in range(N):
    g=tri(1,1.5,2.35); b=tri(.1,.2,.35); fn=math.exp(random.gauss(0,.3)); ft=tri(.7,1,1.4)
    val={n:(random.random()<p) for n,_,_,_,_,med,p in BASE if not med}
    k=tri(.5,1,1.3); rs.append((g,b,fn,ft,val,k))
def vol(M,O,x):
    g,b,fn,ft,val,k=x; Oe=O*k
    can=armar(g,b,fn,ft,val)
    return volumen_con(M*1e6/30-cp(Oe),can)[1]+Oe
def P(v,t): return sum(1 for x in v if x>=t)/len(v)
out['metas']={}
for O in (0,200):
    for M in (51,61):
        v=[vol(M,O,x) for x in rs]; v.sort()
        out['metas'][f'{O}_{M}']=dict(p700=P(v,700),p850=P(v,850),p880=P(v,880),p1000=P(v,1000),med=v[len(v)//2],p10=v[int(.1*len(v))],p90=v[int(.9*len(v))])
        print(O,M,{k:round(x,2) for k,x in out['metas'][f'{O}_{M}'].items()})
# ruta (con 200 propios y 51 M)
v1=[(vol(51,200,x),x) for x in rs]
def cond(f): 
    s=[a for a,x in v1 if f(x)]; return (P(s,1000),len(s))
tik=lambda x:x[4]['TikTok']; todas=lambda x:all(x[4].values())
out['ruta']=dict(hoy=cond(lambda x:True),tiktok=cond(tik),cuatro=cond(todas),g15=cond(lambda x:todas(x) and x[0]>=1.5),techo=cond(lambda x:todas(x) and x[0]>=1.5 and x[3]>=1.0),
                 propios=cond(lambda x:todas(x) and x[0]>=1.5 and x[3]>=1.0 and x[5]>=1.0))
print(out['ruta'])
json.dump(out,open('analisis/escenarios_propios_2027.json','w'),indent=1)
