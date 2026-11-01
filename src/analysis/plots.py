"""Paper figures from completed-model analysis; no inference or retuning."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
def main():
    rows=list(csv.DictReader((ROOT/'results/processed/budget_curves.csv').open()))
    models=list(dict.fromkeys(r['model'] for r in rows))
    methods=['random','coverage','tool_name','policy']
    colors=['#555555','#0072B2','#E69F00','#009E73']
    plt.rcParams.update({'font.size':12,'xtick.labelsize':11,'ytick.labelsize':11,'axes.titlesize':11,'legend.fontsize':11})
    fig,axes=plt.subplots(2,len(models),figsize=(3*len(models),5.8),squeeze=False,sharex=True,sharey=True)
    for j,model in enumerate(models):
        for k,qualified in enumerate([False,True]):
            ax=axes[k,j]
            for method,color,marker in zip(methods,colors,['o','s','^','D']):
                rr=[r for r in rows if r['model']==model and r['method']==method]
                n=int(rr[0]['qualified_campaigns' if qualified else 'campaigns'])
                if n:
                    ax.plot([int(r['budget']) for r in rr],[int(r['qualified_detected' if qualified else 'detected'])/n for r in rr],label=method,color=color,marker=marker,alpha=.85)
            label={'qwen05':'Qwen2.5-0.5B','qwen15':'Qwen2.5-1.5B','smol17':'SmolLM2-1.7B'}[model]
            ax.set_title(label+'\n'+('Clean-qualified' if qualified else 'All campaigns'))
            ax.set_xticks([1,2,4,8]);ax.set_ylim(-.03,1.03);ax.grid(alpha=.2)
            if j==0:ax.set_ylabel('Campaign detection fraction')
            if k==1:ax.set_xlabel('Logical workflow queries')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=4 if len(models)>1 else 2,frameon=False)
    fig.tight_layout(rect=[0,.10,1,1])
    out=ROOT/'results'/'figures';out.mkdir(exist_ok=True)
    for extension in ['png','svg']:fig.savefig(out/('budget_curves.'+extension),dpi=200,bbox_inches='tight')
    plt.close(fig)
    print('Wrote budget_curves.png and .svg for '+', '.join(models))
if __name__=='__main__':main()
