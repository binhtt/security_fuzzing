"""Reproduce the publication figure from the reported, audited counts."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
P=Path(__file__).resolve().parent
q=np.array([1,2,4,8])
raw={"Qwen2.5-0.5B":[5,5,5,5],"Qwen2.5-1.5B":[5,5,5,5],"SmolLM2-1.7B":[6,7,7,7]}
strict_n={"Qwen2.5-0.5B":10,"Qwen2.5-1.5B":5,"SmolLM2-1.7B":4}
methods=["Random","Rarity","Tool-name","Policy-effect"]
planner=np.array([2,3,3,3]); final=np.array([0,0,0,0])
records=[]
for model,counts in raw.items():
 for b,n in zip(q,counts):
  records.append(dict(panel="a",study="primary",measure="raw_final_detection",group=model,query=int(b),count=int(n),denominator=25))
  records.append(dict(panel="a",study="primary",measure="strict_final_detection",group=model,query=int(b),count=0,denominator=strict_n[model]))
for m,p,f in zip(methods,planner,final):
 for measure,count in [("violating_planner_proposal",p),("final_policy_violation",f)]:
  records.append(dict(panel="b",study="expanded_7B",measure=measure,group=m,query="",count=int(count),denominator=120))
with (P/"figure_data.csv").open("w",newline="") as h:
 w=csv.DictWriter(h,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
assert len(records)==32 and all(r["count"]<=r["denominator"] for r in records)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.labelsize":11,
 "xtick.labelsize":10.5,"ytick.labelsize":10.5,"legend.fontsize":10.5,
 "axes.titlesize":11.5,"pdf.fonttype":42,"ps.fonttype":42,
 "svg.fonttype":"none","axes.linewidth":.7,"xtick.major.width":.7,
 "ytick.major.width":.7,"savefig.facecolor":"white"})
blue="#0072B2";orange="#D55E00";black="#202020"
fig,axes=plt.subplots(1,2,figsize=(160/25.4,75/25.4))
fig.subplots_adjust(left=.092,right=.99,bottom=.22,top=.87,wspace=.36)
a,b=axes
for ax in axes:
 ax.spines[["top","right"]].set_visible(False)
 ax.set_axisbelow(True);ax.grid(axis="y",color="#DEDEDE",linewidth=.55)
 ax.tick_params(direction="out",length=3)
a.axvspan(.8,2.2,color="#F0F0F0",zorder=0)
a.text(1.5,10,"Shared prefix",ha="center",va="center",rotation=90,fontsize=10.5,color="#555555")
a.plot(q,np.array(raw["Qwen2.5-0.5B"])/25*100,color=blue,ls="--",lw=1.35,marker="s",ms=4.5,
 label="Qwen2.5 (0.5B, 1.5B)")
a.plot(q,np.array(raw["SmolLM2-1.7B"])/25*100,color=orange,lw=1.35,marker="o",ms=4.5,label="SmolLM2: 1.7B")
a.plot(q,np.zeros(4),color=black,ls=":",lw=1.35,marker="^",ms=4.5,label="Strict-qualified (all)")
a.set(xlim=(.8,8.3),ylim=(-1.2,35),xticks=q,yticks=[0,10,20,30],
 xlabel="Adversarial queries",ylabel="Detected runs (%)")
a.set_title("(a) Primary study",loc="left",pad=9,fontweight="bold")
a.legend(loc="lower right",bbox_to_anchor=(1.01,.10),frameon=False,
 handlelength=1.8,handletextpad=.5,borderaxespad=0,labelspacing=.4,fontsize=10.5)
xx=np.arange(4);w=.34
b.bar(xx-.18,planner,w,color=blue,edgecolor=black,linewidth=.65,hatch="///",zorder=3)
b.scatter(xx+.18,final,s=27,facecolors="white",edgecolors=orange,linewidths=1.2,zorder=4)
for i,p in enumerate(planner):
 b.text(i-.18,p+.1,str(p),ha="center",va="bottom",fontsize=10.5,color=black)
 b.text(i+.18,.12,"0",ha="center",va="bottom",fontsize=10.5,color=orange)
b.set(xlim=(-.6,3.6),ylim=(-.16,4.65),yticks=[0,1,2,3,4],
 xticks=xx,xticklabels=["Random","Rarity","Tool","Policy"],
 xlabel="Selection strategy",ylabel="Violations / 120 workflows")
b.set_title("(b) Expanded 7B study",loc="left",pad=9,fontweight="bold")
b.legend(handles=[Patch(facecolor=blue,edgecolor=black,hatch="///",linewidth=.65,label="Planner proposal"),
 Line2D([0],[0],color=orange,marker="o",markerfacecolor="white",ls="None",markersize=5,label="Final action")],
 loc="upper left",frameon=False,handlelength=1.5,handletextpad=.5,borderaxespad=.3,labelspacing=.4,fontsize=10.5)
for ext in ["pdf","svg","png"]:
 fig.savefig(P/f"sf_experimental_results.{ext}",dpi=600)
plt.close(fig)
(P/"figure_notes.json").write_text(json.dumps({
 "size_mm":[160,75],"png_dpi":600,"pdf_fonttype":42,
 "sources":["Primary results supplied with the manuscript","Audited SF_expanded_results.tex"],
 "interpretation":"Panel a shows detection across case-seed runs; panel b shows role-level violations across workflows. Panels have different denominators. All four selectors share the panel-a curves. No confidence intervals or independent-replication claim.",
 "strict_denominators":strict_n,"budget12":"Exploratory 0.5B pilot described in text; it is not a matched 7B budget comparison."},indent=2))
